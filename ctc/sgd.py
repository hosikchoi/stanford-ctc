import numpy as np
import pickle

class SGD:

    def __init__(self,model,alpha=1e-2,optimizer='momentum',momentum=0.9):
        self.model = model

        assert self.model is not None, "Must define a function to optimize"
        self.it = 0
        self.momentum = momentum # momentum
        self.alpha = alpha # learning rate
	self.optimizer = optimizer
	if self.optimizer == 'momentum' or self.optimizer == 'nesterov':
	    print "Using %s.."%self.optimizer
	    self.velocity = [[np.zeros(w.shape),np.zeros(b.shape)] 
			      for w,b in self.model.stack]
	elif self.optimizer == 'adagrad' or self.optimizer == 'adadelta':
	    print "Using %s.."%self.optimizer
	    self.gradt = [[np.zeros(w.shape),np.zeros(b.shape)] 
			      for w,b in self.model.stack]
	elif self.optimizer == 'sgd':
	    print "Using sgd.."
	else:
	    raise ValueError("Invalid optimizer")

	self.costt = []
	self.expcost = []

    def run_seq(self,data_dict,alis,keys,sizes):
        """
        Runs stochastic gradient descent with model as objective.
        Uses single utterances instead of minibatches
        """

        # momentum setup
        momIncrease = 10
        mom = 0.5

        # randomly permute utterance order
        perm = np.random.permutation(range(len(keys)))

        for i in perm:
            k = keys[i]

            self.it += 1

            mb_data = data_dict[k]
            # convert the list of string phone ids to int vector
            mb_labels = np.array(alis[k],dtype=np.int32)

	    if self.optimizer == 'nesterov':
		# w = w+mom*velocity (evaluate gradient at future point)
		self.model.updateParams(mom,self.velocity)
                
            cost,grad = self.model.costAndGrad(mb_data,mb_labels)

	    # undo update
	    if self.optimizer == 'nesterov':
		# w = w-mom*velocity
		self.model.updateParams(-mom,self.velocity)

	    # compute exponentially weighted cost
	    if self.it > 1:
		self.expcost.append(.01*cost + .99*self.expcost[-1])
	    else:
		self.expcost.append(cost)

	    if self.optimizer == 'momentum':
		if self.it > momIncrease:
		    mom = self.momentum
		# velocity = mom*velocity + eta*grad
		self.velocity = [[mom*vs[0]+self.alpha*g[0],mom*vs[1]+self.alpha*g[1]]
				  for vs,g in zip(self.velocity,grad)]
		update = self.velocity
		scale = -1.0

	    elif self.optimizer == 'adagrad':
		epsilon = 1e-8
		# trace = trace+grad.^2
		self.gradt = [[gt[0]+g[0]*g[0]+epsilon,gt[1]+g[1]*g[1]+epsilon] 
			for gt,g in zip(self.gradt,grad)]
		# update = grad.*trace.^(-1/2)
		update =  [[g[0]*(1./np.sqrt(gt[0])),g[1]*(1./np.sqrt(gt[1]))]
			for gt,g in zip(self.gradt,grad)]
		scale = -self.alpha

	    elif self.optimizer == 'nesterov':
		# velocity = mom*velocity - alpha*grad
		self.velocity = [[mom*vs[0]-self.alpha*g[0],mom*vs[1]-self.alpha*g[1]]
				  for vs,g in zip(self.velocity,grad)]
		update = self.velocity
		scale = 1.0

	    elif self.optimizer == 'adadelta':
		epsilon = 1e-9
		gamma = 1.-(100./(1000.+self.it))
		print "Gamma is %f"%gamma
		# trace = trace+grad.^2
		self.gradt = [[gamma*gt[0]+g[0]*g[0]+epsilon,gamma*gt[1]+g[1]*g[1]+epsilon] 
			for gt,g in zip(self.gradt,grad)]
		# update = grad.*trace.^(-1/2)
		update =  [[g[0]*(1./np.sqrt(gt[0])),g[1]*(1./np.sqrt(gt[1]))]
			for gt,g in zip(self.gradt,grad)]
		scale = -self.alpha

	    elif self.optimizer == 'sgd':
		update = grad
		scale = -self.alpha

	    # update params
	    self.model.updateParams(scale,update)

	    self.costt.append(cost)
            if self.it%1 == 0:
		print "Iter %d : Cost=%.4f, ExpCost=%.4f, SeqLen=%d, NumFrames=%d."%(self.it,
			cost,self.expcost[-1],mb_labels.shape[0],mb_data.shape[1])
            