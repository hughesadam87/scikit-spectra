"""
Adapted to fit skspec 5/6/2013.  Original credit to Alexis Mignon:

Module for Principal Component Analysis.

Features:
* pca and kernel pca
* pca through singular value decomposition (SVD)

Author: Alexis Mignon (c)
Date: 10/01/2012
e-mail: alexis.mignon@gmail.com
"""

import numpy as np
from scipy.sparse.linalg.eigen.arpack import eigs
from scipy.linalg import eigh

def full_pca(data):
    """
    Performs the complete eigen decomposition of
    the covariance matrix.
    
    arguments:
    * data: 2D numpy array where each row is a sample and
        each column a feature.
    
    return:
    * w: the eigen values of the covariance matrix sorted in from 
          highest to lowest.
    * u: the corresponding eigen vectors. u[:,i] is the vector
         corresponding to w[i]
         
    Notes: If you want to compute only a few number of principal
           components, you should consider using 'pca' or 'svd_pca'.
    """
    cov = np.cov(data.T)
    w,u = eigh(cov,overwrite_a = True)
    return w[::-1],u[:,::-1]

def pca(data,k):
    """
    Performs the eigen decomposition of the covariance matrix.
    
    arguments:
    * data: 2D numpy array where each row is a sample and
            each column a feature.
    * k: number of principal components to keep.
    
    return:
    * w: the eigen values of the covariance matrix sorted in from 
          highest to lowest.
    * u: the corresponding eigen vectors. u[:,i] is the vector
         corresponding to w[i]
         
    Notes: If the number of samples is much smaller than the number
           of features, you should consider the use of 'svd_pca'.
    """
    cov = np.cov(data.T)
    # kw "which" means return largest magnitude k eigenvalues
    w,u = eigs(cov,k = k,which = 'LM')
#    return w[::-1],u[:,::-1]
    return w,u #(No need to reverse w,u because eigs does it using 'LM')

def extern_pca(data,k):
    """
    Performs the eigen decomposition of the covariance matrix based
    on the eigen decomposition of the exterior product matrix.
    
    
    arguments:
    * data: 2D numpy array where each row is a sample and
            each column a feature.
    * k: number of principal components to keep.
    
    return:
    * w: the eigen values of the covariance matrix sorted in from 
          highest to lowest.
    * u: the corresponding eigen vectors. u[:,i] is the vector
         corresponding to w[i]
         
    Notes: This function computes PCA, based on the exterior product
           matrix (C = X*X.T/(n-1)) instead of the covariance matrix
           (C = X.T*X) and uses relations based of the singular
           value decomposition to compute the corresponding the
           final eigen vectors. While this can be much faster when 
           the number of samples is much smaller than the number
           of features, it can lead to loss of precisions.
           
           The (centered) data matrix X can be decomposed as:
                X.T = U * S * v.T
           On computes the eigen decomposition of :
                X * X.T = v*S^2*v.T
           and the eigen vectors of the covariance matrix are
           computed as :
                U = X.T * v * S^(-1)
    """
   
#    raise NotImplementedError('Need to curate this method')
    # Should I take last line and remove the [::-1] stuff?
    data_m = data - data.mean(0)
    K = np.dot(data_m,data_m.T)
    w,v = eigs(K,k = k,which = 'LM')
    U = np.dot(data.T,v/np.sqrt(w))
    # Normalizes eigenvalues by length of data (?)
#    return w[::-1]/(len(data)-1),U[:,::-1]
    return w/(len(data)-1),U

def full_kpca(data):
    """
        Performs the complete eigen decomposition of a kernel matrix.
        
        arguments:
        * data: 2D numpy array representing the symmetric kernel matrix.
        
        return:
        * w: the eigen values of the covariance matrix sorted in from 
              highest to lowest.
        * u: the corresponding eigen vectors. u[:,i] is the vector
             corresponding to w[i]
             
        Notes: If you want to compute only a few number of principal
               components, you should consider using 'kpca'.
    """
    w,u = eigh(data,overwrite_a = True)
#    return w[::-1],u[:,::-1]
    return w,u


def kpca(data,k):
    """
        Performs the eigen decomposition of the kernel matrix.
        
        arguments:
        * data: 2D numpy array representing the symmetric kernel matrix.
        * k: number of principal components to keep.
        
        return:
        * w: the eigen values of the covariance matrix sorted in from 
              highest to lowest.
        * u: the corresponding eigen vectors. u[:,i] is the vector
             corresponding to w[i]
             
        Notes: If you want to perform the full decomposition, consider 
               using 'full_kpca' instead.
    """
    w,u = eigs(data,k = k,which = 'LM')
#    return w[::-1],u[:,::-1]
    return w,u

class PCA(object):
    """
        PCA object to perform Principal Component Analysis.
    """
    def __init__(self,k = None, kernel = False, extern = False):
        """
        Constructor.
        
        arguments:
        * k: number of principal components to compute. 'None'
             (default) means that all components are computed.
        * kernel: perform PCA on kernel matrices (default is False)
        * extern: use extern product to perform PCA (default is 
               False). Use this option when the number of samples
               is much smaller than the number of features.

        Notes:
        * All data will be mean-cenetered.  Np subroutines (eg np.cov())
          do this in all cases except for the extern_pca() method, which
          does this automatically.
        """
    
        self._k = k #THESE SHOULD BE PROPERTIES
        self._kernel = kernel
        self._extern = extern
        
    
    def fit(self,X):
        """
        Performs PCA on the data array X.
        arguments:
        * X: 2D numpy array. In case the array represents a kernel
             matrix, X should be symmetric. Otherwise each row
             represents a sample and each column represents a
             feature.
        """
        
        # Mean centering is inherently performed in numpy methods that compute
        # the covariance.  This does it additionally because X may not be
        # the same matrix used to fit the original data
        
        # If number principle componenets is not specified, full pca or kpca
        if self._k is None :
            if self._kernel :
                pca_func = full_kpca
            else :
                pca_func = full_pca
            self.eigen_values_,self.eigen_vectors_ = pca_func(X)

        # If specifying number of principle components
        else :
            if self._kernel :
                pca_func = kpca
            elif self._extern :
                pca_func = extern_pca
            else :
                pca_func = pca
            self.eigen_values_,self.eigen_vectors_ = pca_func(X,self._k)
        
        if self._kernel :
            
            total_variance = X.diagonal().sum()

            
        # If not kernal pca, subtract mean.
        # Total variance is squared difference from mean, since mean centered.
        # Simply computes variance of each element
        else :
            self.mean = X.mean(0)
            diff = X - self.mean
            total_variance = (diff*diff).sum()/(X.shape[0]-1)

        # Scikit image also has this; how much variance each component
        # can account for.  Should sum to 1 if all components used.
        self.explained_variance_ = self.eigen_values_.sum()/total_variance
        return self
    
        
    def transform(self,X,whiten = False):
        """
        Project data on the principal components. If the whitening
        option is used, components will be normalized to that they
        have the same contribution.
        
        arguments:
        * X: 2D numpy array of data to project.
        * whiten: (default is False) all components are normalized
            so that they have the same contribution.
            
        returns:
        * prX : projection of X on the principal components.
        
        Notes: In the case of Kernel PCA, X[i] represents the value
           of the kernel between sample i and the j-th sample used
           at train time. Thus, if fit was called with a NxN kernel
           matrix, X should be a MxN matrix.
           
           The projection in the kernel case is made to be equivalent
           to the projection in the linear case.
           
               X.T = U * S * v.T
               C = 1/(N-1) * X.T * X
               X.T * X = U*S^2*U.T
               K = X * X.T = v*S^2*v.T
               
               U = X.T * v * S^(-1)
           
           The projection with PCA is :
               X' = X * U
               X' = X * X.T * v * S^(-1)
               X' = K * v * S^(-1)
               
           For whiten PCA :
               X' = X * U * S^(-1) * sqrt(N-1)
               X' = X * X.T * v * S^(-1) * S^(-1) * sqrt(N-1)
               X' = K * S^(-2) * sqrt(N-1)
        """
    
        
        if self._kernel :
            pr = np.dot(X,self.eigen_vectors_)
            if whiten :
                pr /= self.eigen_values_ / np.sqrt(X.shape[0]-1)
            else :
                pr /= np.sqrt(self.eigen_values_)
        else :
            pr = np.dot(X - self.mean,self.eigen_vectors_)
            if whiten:
                pr /= np.sqrt(self.eigen_values_)
        return pr
    
        