import numpy as np
from numpy.lib.stride_tricks import as_strided

class Convolution():
  def __init__(self,filter_size):
    self.filter_height,self.filter_width=filter_size
    self.padding=1
    self.stride=1

  def get_patches(self,image_array,pool=False):
    self.image_array=image_array
    print(self.image_array.shape)
    self.batch_size,self.image_height,self.image_width= self.image_array.shape
    if pool==True:
      self.stride=2
      self.filter_height=2
      self.filter_width=2
    else:
      self.stride=1
      self.filter_height=3
      self.filter_width=3
    self.new_height=(self.image_height-self.filter_height)//self.stride + 1
    self.new_width=(self.image_width-self.filter_width)//self.stride + 1
    self.new_shape=(self.batch_size,self.new_height,self.new_width,self.filter_height,self.filter_width)
    self.mem_location=(self.image_array.strides[0],self.image_array.strides[1]*self.stride,self.image_array.strides[2]*self.stride,self.image_array.strides[1],self.image_array.strides[2])
    self.patches=as_strided(self.image_array,self.new_shape,self.mem_location)
    return self.patches

  def forward(self,image_array):
    self.image_array=image_array
    self.image_array_padded=np.pad(self.image_array,((0,0),(self.padding,self.padding),(self.padding,self.padding)),mode='constant')
    print(f'image_array_padded{self.image_array_padded.shape}')
    self.patches=self.get_patches(self.image_array_padded)
    self.patches_reshaped=self.patches.reshape(self.patches.shape[0],self.patches.shape[1],self.patches.shape[2],self.filter_height*self.filter_width)
    print(f'patches{self.patches.shape}')
    print(f'patches_reshaped{self.patches_reshaped.shape}')
    self.filter_vertical=np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
    self.filter_vertical=self.filter_vertical.reshape(9,1)
    self.filter_horizontal=np.array([[-1,-2,-1],[0,0,0],[1,2,1]]) #self initialized sobel filter because its simple cnn task so why waste computation
    self.filter_horizontal=self.filter_vertical.reshape(9,1)
    #print(f'patches{self.patches.shape}')
    print(f'patches_reshaped{self.patches_reshaped.shape}')
    self.edge_vertical=np.tensordot(self.patches_reshaped,self.filter_vertical,axes=([3],[0]))
    self.edge_horizontal=np.tensordot(self.patches_reshaped,self.filter_horizontal,axes=([3],[0]))
    self.edge=np.sqrt(np.square(self.edge_vertical)+np.square(self.edge_horizontal))
    self.edge=self.edge.reshape(self.patches.shape[0],self.patches.shape[1],self.patches.shape[2])
    self.patches2=self.get_patches(self.edge,pool=True)  #say poolsize is different but wanna use only one function
    print(f'patches2{self.patches2.shape}')
    #self.patches2=self.patches2.reshape(self.patches.shape[0],self.patches.shape[1],self.patches.shape[2],9)
    self.patches2=self.patches2.reshape(self.patches.shape[0],self.patches.shape[1],self.patches.shape[2],self.patches.shape[3]*self.patches.shape[4])

    #print(f'patches2{self.patches2.shape}')
    # print(f'patches{self.patches[0][0][0]}')
    #print(f'patches ko shape{self.patches2.shape}')


    self.output=np.max(self.patches2,axis=3)
    #print(f'output of pool{self.output.shape}')
    # self.output=self.output.reshape(self.batch_size,self.output_height,self.output_width)
    del self.patches, self.patches_reshaped, self.edge, self.patches2,self.filter_vertical,self.filter_horizontal,self.edge_vertical,self.edge_horizontal

    return self.output.reshape(self.output.shape[0],-1)

class Dense():
    def __init__(self, ninputs, nnodes,activation=None ):

        self.weight = np.random.randn(ninputs, nnodes) * np.sqrt(2. / ninputs) #xaiver initialization
        self.bias = np.random.rand(nnodes) * 0.01
        self.sdw = np.zeros((ninputs, nnodes))
        self.sdb = np.zeros(nnodes)
        self.vdw = np.zeros((ninputs, nnodes))
        self.vdb = np.zeros(nnodes)
        self.t = 0
        self.activation=activation

    def forward(self, inputs):
        self.input = inputs
        self.output = np.dot(inputs, self.weight) + self.bias
        if self.activation:
          self.output=self.activation.forward(self.output)
        return self.output

    def backward(self, gradient):
        if self.activation:
          gradient=self.activation.backward(gradient)
        self.gradient_weight = np.dot(self.input.T, gradient)
        self.gradient_bias = np.sum(gradient, axis=0)
        self.gradient_input = np.dot(gradient, self.weight.T)


        return self.gradient_input

    def calculate(self, optimizer):
        if optimizer == 'adam':
            self.t += 1
            beta1, beta2 = 0.9, 0.999
            epsilon = 1e-8

            self.sdw = beta2 * self.sdw + (1 - beta2) * (self.gradient_weight ** 2)
            self.sdb = beta2 * self.sdb + (1 - beta2) * (self.gradient_bias ** 2)

            self.vdw = beta1 * self.vdw + (1 - beta1) * self.gradient_weight
            self.vdb = beta1 * self.vdb + (1 - beta1) * self.gradient_bias

            # Bias correction for adam optimizer for the starting difference while using exponantially weighted average
            sdw_corrected = self.sdw / (1 - beta2 ** self.t)
            sdb_corrected = self.sdb / (1 - beta2 ** self.t)
            vdw_corrected = self.vdw / (1 - beta1 ** self.t)
            vdb_corrected = self.vdb / (1 - beta1 ** self.t)

            self.sdw_corrected = sdw_corrected
            self.sdb_corrected = sdb_corrected
            self.vdw_corrected = vdw_corrected
            self.vdb_corrected = vdb_corrected

    def update(self, learning_rate, optimizer):
        if optimizer == 'adam':
            self.weight -= learning_rate * self.vdw_corrected / (np.sqrt(self.sdw_corrected) + 1e-8)
            self.bias -= learning_rate * self.vdb_corrected / (np.sqrt(self.sdb_corrected) + 1e-8)
        else:
            self.weight -= learning_rate * self.gradient_weight
            self.bias -= learning_rate * self.gradient_bias

    def l2(self):
        return np.sum(self.weight ** 2)

class Relu():
    def forward(self, inputs):
        self.input = inputs
        self.output = np.maximum(0, inputs)
        return self.output

    def backward(self, gradients):
        self.gradient = gradients * (self.input > 0) #why not self.output>>>because we need a boolean return
        return self.gradient


class Softmax():
    def __init__(self,final=False):
        self.final = final
    def forward(self, inputs):
        self.input = inputs
        exp = np.exp(inputs - np.max(inputs, axis=1, keepdims=True))
        probabilities = exp / np.sum(exp, axis=1, keepdims=True)
        self.output = probabilities
        return self.output

    def backward(self, gradient):
      if self.final == True:
        return gradient
      else:
        self.dinputs = gradient * self.output * (1 - self.output)  # Derivative of softmax
        return self.dinputs

class CategoricalCrossEntropyLoss():
    def forward(self, probs, true_outputs, layers,lamda=0):
        clipped_probs = np.clip(probs, 1e-7, 1 - 1e-7)
        loss_data = -np.sum(true_outputs * np.log(clipped_probs)) / (len(true_outputs) + 1e-8)

        # l2_terms = [lamda * np.sum(layer.l2()) for layer in layers]
        # loss_weight = 0.5 * np.sum(l2_terms) / (len(true_outputs) +  1e-8)
        return loss_data

    def accuracy(self, probs, true_outputs):

        prediction=np.argmax(probs, axis=1)
        true_label=np.argmax(true_outputs, axis=1)
        accuracy=np.mean(prediction == true_label)
        return accuracy

    def backward(self, probs, true_outputs):
        samples = len(true_outputs)

        self.dinputs = (probs - true_outputs) / samples
        return self.dinputs

import pickle
class NeuralNetwork():
  def __init__(self,loss_function='CategoricalCrossEntropyLoss()',optimizer='adam',learning_rate=0.001):
     self.conv=[]
     self.conv2=[]
     self.layers=[]
     self.loss_function = loss_function
     self.learning_rate = learning_rate
     self.optimizer = optimizer


  def add(self,layer,grad=True):
    if grad==True:
      self.layers.append(layer)
    else:
      self.conv.append(layer)
      self.conv2.append(layer)


  def fit(self, X_train, y_train,batch_size,epochs=10):
      self.epochs=epochs
      for convu in self.conv:
          X_train= convu.forward(X_train)
      for epoch in range(self.epochs):
          epoch_loss = 0
          epoch_loss_val = 0
          for i in range(0, len(X_train), batch_size):
              batch_inputs = X_train[i:i + batch_size]

              batch_true_outputs = y_train[i:i + batch_size]


              x = batch_inputs

              #print(f'x ko shape{x.shape}')
              for layer in self.layers:
                  x = layer.forward(x)
                  #print(x.shape)


              loss = self.loss_function.forward(x, batch_true_outputs, self.layers)
              epoch_loss += loss  # Accumulate batch loss

              gradient = self.loss_function.backward(x, batch_true_outputs)
              for layer in reversed(self.layers):
                  # print(f'gradient is {gradient.shape}')


                  gradient = layer.backward(gradient)
                  # print(f'gradient is {gradient.shape}')

              for layer in self.layers:

                layer.calculate(self.optimizer)

              for layer in self.layers:

                layer.update(self.learning_rate, self.optimizer)


          print(f"Epoch {epoch + 1}, Loss: {epoch_loss / len(X_train) * batch_size}")  # Print average loss for the epoch
          epoch_accuracy = 0
          epoch_loss_val = 0
          # for i in range(0,len(X_test),batch_size):
          #     batch_validate = X_test[i:i + batch_size]
          #     batch_validate_true = y_test[i:i + batch_size]

  def eval(self,X_test,y_test):
          x2=X_test
          for convu in self.conv2:
            x2=convu.forward(x2)
          for layer in self.layers:
              x2=layer.forward(x2)

          loss_validate = self.loss_function.forward(x2, y_test, self.layers)
          accurate=self.loss_function.accuracy(x2, y_test)

          print(f"val_Loss: {loss_validate},val_accuracy:{accurate}")


  def save_model(self, filename):
        """Saves the current model to a file using pickle."""
        with open(filename, 'wb') as file:
            pickle.dump(self, file)
        print(f"Model saved to {filename}")

  @staticmethod
  def load_model(filename):
        """Loads a model from a file using pickle."""
        with open(filename, 'rb') as file:
            model = pickle.load(file)
        print(f"Model loaded from {filename}")
        return model

