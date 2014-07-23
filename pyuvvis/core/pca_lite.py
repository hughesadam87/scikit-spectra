import numpy as np
from scipy import linalg

def array2d(X, dtype=None, order=None):
    """Returns at least 2-d array with data from X"""
    return np.asarray(np.atleast_2d(X), dtype=dtype, order=order)

def as_float_array(X, copy=True):
    """Converts an array-like to an array of floats

    The new dtype will be np.float32 or np.float64, depending on the original
    type. The function can create a copy or modify the argument depending
    on the argument copy.

    Parameters
    ----------
    X : array

    copy : bool, optional
        If True, a copy of X will be created. If False, a copy may still be
        returned if X's dtype is not a floating point type.

    Returns
    -------
    X : array
        An array of type np.float
    """
    if isinstance(X, np.matrix):
        X = X.A
    elif not isinstance(X, np.ndarray) and not sp.issparse(X):
        return safe_asarray(X, dtype=np.float64)
    if X.dtype in [np.float32, np.float64]:
        return X.copy() if copy else X
    if X.dtype == np.int32:
        X = X.astype(np.float32)
    else:
        X = X.astype(np.float64)
    return X

class PCAError(Exception):
    """ """


# REPLACE V WITH VT TO BE CLOSER IN NOTATION TO NODA BOOK
class PCA():
    """Principal component analysis (PCA)

    Linear dimensionality reduction using Singular Value Decomposition of the
    data and keeping only the most significant singular vectors to project the
    data to a lower dimensional space.

    This implementation uses the scipy.linalg implementation of the singular
    value decomposition. It only works for dense arrays and is not scalable to
    large dimensional data.

    The time complexity of this implementation is ``O(n ** 3)`` assuming
    n ~ n_samples ~ n_features.

    Parameters
    ----------
    n_components : int, None or string
        Number of components to keep.
        if n_components is not set all components are kept::

            n_components == min(n_samples, n_features)

        if n_components == 'mle', Minka\'s MLE is used to guess the dimension
        if ``0 < n_components < 1``, select the number of components such that
        the amount of variance that needs to be explained is greater than the
        percentage specified by n_components

    copy : bool
        If False, data passed to fit are overwritten

    whiten : bool, optional
        When True (False by default) the `components_` vectors are divided
        by n_samples times singular values to ensure uncorrelated outputs
        with unit component-wise variances.

        Whitening will remove some information from the transformed signal
        (the relative variance scales of the components) but can sometime
        improve the predictive accuracy of the downstream estimators by
        making there data respect some hard-wired assumptions.

    Attributes
    ----------
    `components_` : array, [n_components, n_features]
        Components with maximum variance.

    `explained_variance_ratio_` : array, [n_components]
        Percentage of variance explained by each of the selected components. \
        k is not set then all components are stored and the sum of explained \
        variances is equal to 1.0

    Notes
    -----
    For n_components='mle', this class uses the method of `Thomas P. Minka:
    Automatic Choice of Dimensionality for PCA. NIPS 2000: 598-604`

    Due to implementation subtleties of the Singular Value Decomposition (SVD),
    which is used in this implementation, running fit twice on the same matrix
    can lead to principal components with signs flipped (change in direction).
    For this reason, it is important to always use the same estimator object to
    transform data in a consistent fashion.

    Examples
    --------

    >>> import numpy as np
    >>> from sklearn.decomposition import PCA
    >>> X = np.array([[-1, -1], [-2, -1], [-3, -2], [1, 1], [2, 1], [3, 2]])
    >>> pca = PCA(n_components=2)
    >>> pca.fit(X)
    PCA(copy=True, n_components=2, whiten=False)
    >>> print pca.explained_variance_ratio_ # doctest: +ELLIPSIS
    [ 0.99244...  0.00755...]

    See also
    --------
    ProbabilisticPCA
    RandomizedPCA
    KernelPCA
    SparsePCA
    """
    # Turn off copy?
    def __init__(self, n_components=None, copy=True, whiten=False):
        self.n_components = n_components
        self.copy = copy
        self.whiten = whiten
        
        self._U = None
        self._S = None
        self._VT = None
        
    def fit(self, X, y=None, **params):
        """Fit the model with X.

        Parameters
        ----------
        X: array-like, shape (n_samples, n_features)
            Training data, where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        self._fit(X, **params)
        return self

    def fit_transform(self, X, y=None, **params):
        """Fit the model with X and apply the dimensionality reduction on X.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            Training data, where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        X_new : array-like, shape (n_samples, n_components)

        """
        U, S, VT = self._fit(X, **params)
        U = U[:, :self.n_components]

        if self.whiten:
            # X_new = X * V / S * sqrt(n_samples) = U * sqrt(n_samples)
            U *= np.sqrt(X.shape[0])
        else:
            # X_new = X * V = U * S * V^T * V = U * S
            U *= S[:self.n_components]

        return U

    # REPLACE V WITH VT TO BE CLOSER IN NOTATION TO NODA BOOK
    def _fit(self, X):
        X = array2d(X)
        n_samples, n_features = X.shape
        X = as_float_array(X, copy=self.copy)
        # Center data
        self.mean_ = np.mean(X, axis=0) #When transposed, this works fine
        X -= self.mean_
        U, S, VT = linalg.svd(X, full_matrices=False)
        self.explained_variance_ = (S ** 2) / n_samples
        self.explained_variance_ratio_ = self.explained_variance_ / \
                                        self.explained_variance_.sum()

        if self.whiten:
            self.components_ = VT / S[:, np.newaxis] * np.sqrt(n_samples)
        else:
            self.components_ = VT

        if self.n_components == 'mle':
            if n_samples < n_features:
                raise ValueError("n_components='mle' is only supported "
                "if n_samples >= n_features")
            self.n_components = _infer_dimension_(self.explained_variance_,
                                            n_samples, n_features)

        elif (self.n_components is not None
              and 0 < self.n_components
              and self.n_components < 1.0):
            # number of components for which the cumulated explained variance
            # percentage is superior to the desired threshold
            ratio_cumsum = self.explained_variance_ratio_.cumsum()
            self.n_components = np.sum(ratio_cumsum < self.n_components) + 1

        if self.n_components is not None:
            self.components_ = self.components_[:self.n_components, :]
            self.explained_variance_ = \
                    self.explained_variance_[:self.n_components]
            self.explained_variance_ratio_ = \
                    self.explained_variance_ratio_[:self.n_components]

        self._U = U
        self._S = S
        self._VT = VT
        
        return (U, S, VT)
    


    @property
    def U(self):
        """ Score matrix (in Noda = W) """
        if self._U is None:
            raise PCAError("Please run .fit() to set U, S, VT from SVD.")
        return self._U
        

    @property
    def S(self):
        """ """
        if self._S is None:
            raise PCAError("Please run .fit() to set U, S, VT from SVD.")       
        return self._S        
        
    @property
    def VT(self):
        """ Loading Vectors """        
        if self._VT is None:
            raise PCAError("Please run .fit() to set U, S, VT from SVD.")
        return self._VT
    
    @property
    def W(self):
        """ Score matrix"""
        return self.U * self.S #ok?

    def transform(self, X):
        """Apply the dimensionality reduction on X.

        Parameters
        ----------
        X : array-like, shape (n_samples, n_features)
            New data, where n_samples in the number of samples
            and n_features is the number of features.

        Returns
        -------
        X_new : array-like, shape (n_samples, n_components)

        """
        X_transformed = X - self.mean_
        X_transformed = np.dot(X_transformed, self.components_.T)
        return X_transformed

    def inverse_transform(self, X):
        """Transform data back to its original space, i.e.,
        return an input X_original whose transform would be X

        Parameters
        ----------
        X : array-like, shape (n_samples, n_components)
            New data, where n_samples in the number of samples
            and n_components is the number of components.

        Returns
        -------
        X_original array-like, shape (n_samples, n_features)

        Notes
        -----
        If whitening is enabled, inverse_transform does not compute the
        exact inverse operation as transform.
        """
        return np.dot(X, self.components_) + self.mean_
    

    #def __repr__(self): 
        #return 'YEAHH BOY'