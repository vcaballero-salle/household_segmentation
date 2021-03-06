import numpy as np
from sklearn.cluster import KMeans
import pandas as pd


def integral_seq(ts, dx=0.25):
	'''Integrates load shape ts

	Args:
		ts: time series, 1D np array
		dx: granularity of ts wrt the hour: 0.25 = 15 minute interval data

	Returns a sequence where the kth value is area under time series ts from index 0 to k
	'''
    integral = np.empty_like(ts)
    integral[0] = 0
    for i in range(1, ts.shape[0]):
        integral[i] = integral[i-1] + np.trapz(ts[i-1:i+1], dx=dx)
    return integral[1:]


def integral_kmeans(X, k, load_shapes=False):
	'''Cluster by integral k-means
	
	Args:
		X: 2D np array of load profiles. Dimension (n_loads, 24/interval_length)
		k: Number of cluster

	Returns list of integral k-means cluster assignments for each load in X
	'''

    max_power = X.max(axis = 1)
    interval= 24/float(X.shape[1])

    #Normalize
    total_power = X.sum(axis = 1)
	X_norm = (X.T/total_power).T

    ts_integral = np.apply_along_axis(lambda ts: integral_seq(ts, dx=interval), 1, X_norm)
    ts_integral = np.concatenate((ts_integral, max_power.reshape(max_power.shape[0], 1)), axis=1)
    kmeans = KMeans(n_clusters=k).fit(ts_integral)

    if load_shapes:
    	df = pd.DataFrame(X_norm)
    	df['integ_labels'] = kmeans.labels_
    	return df

    return kmeans.labels_


def twostage_kmeans(X, k_consumption, k_peaktime):
	'''Cluster by two-stage k-means
	
	Args:
		X: 2D np array of load profiles. Dimension (n_loads, 24/interval_length)
		k_consumption: Number of clusters determined by overall consumption
		k_peaktime: Number of clusters determined by time of peak

	Returns list of two-stage k-means cluster assignments for each load in X
	'''

    include_load_shapes=True
    df = integral_kmeans(X, k_consumption, include_load_shapes)

    twostage_labels = []

    for i in range(k_consumption):

        cluster = df.loc[df.integ_labels == i, :].drop(['integ_labels'], axis=1)
        kmeans = KMeans(n_clusters=k_peaktime).fit(cluster)
        twostage_labels = twostage_labels + list(k_peaktime*(i) + kmeans.labels_)

    return twostage_labels