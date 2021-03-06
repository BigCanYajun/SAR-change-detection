import numpy as np
import scipy.stats
import matplotlib.pyplot as plt
import matplotlib.colors
from sar_data import *

class Omnibus(object):
    """
    Implements the Omnibus test statistic
    """

    def __init__(self, sar_list, ENL):
        """
        Create a new Omnibus test
        sar_list should be a list of SARData objects
        ENL is the (common) equivalent number of looks of the images
        """

        self.sar_list = sar_list
        self.ENL = ENL

        p = 3
        k = len(sar_list)
        n = ENL

        self.f = (k-1)*p**2
        self.rho = 1- (2*p**2 - 1)/(6*p*(k-1)) * (k/n - 1/(n*k))

        sum_term = sum([np.log(Xi.determinant()) for Xi in sar_list])
        X = sar_sum(sar_list)

        # Omnibus test
        self.f = (k-1)*p**2
        self.rho = 1 - (2*p**2 - 1)/(6*(k-1)*p) * (k/n - 1/(n*k))
        self.w2 = p**2*(p**2-1)/(24*self.rho**2) * (k/n**2 - 1/((n*k)**2)) - (p**2*(k-1))/4 * (1 - 1/self.rho)**2
        
        self.lnq = n*(p*k*np.log(k) + sum_term - k*np.log(X.determinant()))

    def pvalue(self):
        "Average probability over the tested region"
        chi2 = scipy.stats.chi2.cdf
        z = -2*self.rho*self.lnq
        return 1 - np.mean(chi2(z, df=self.f) + self.w2 * (chi2(z, df=self.f+4) - chi2(z, df=self.f)))

    def histogram(self):
        """
        Histogram of no change region
        and pdf with only chi2 term
        """

        fig = plt.figure(figsize=(8, 4))
        ax = fig.add_subplot(111)
        ax.hist(-2*self.lnq.flatten(), bins=100, normed=True, color="#3F5D7D")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        # Overlay pdf
        p = 3
        k = len(self.sar_list)
        f = (k-1)*p**2
        chi2 = scipy.stats.chi2(f)

        x = np.linspace(0, 100, 1000)
        y = chi2.pdf(x)
        ax.plot(x, y, color="black", linewidth=2)

        ax.set_xlim([0, 100])

        return fig, ax

    def image_binary(self, percent):
        # Select threshold from chi2 percentile (ignore w2 term)
        p = 3
        k = len(self.sar_list)
        f = (k-1)*p**2
        chi2 = scipy.stats.chi2(f)
        threshold = chi2.ppf(1.0 - percent)

        im = np.zeros_like(self.lnq)
        im[-2*self.lnq > threshold] = 1
        return im.reshape(self.sar_list[0].shape)

    def image_autothresholds(self):
        pass

    def image_linear(self, p1, p2):
        pass

    def masked_region(self, mask):
        """
        Extract a subset of the image and test result defined by a mask
        This is similar to using SARData.masked_region() and then RjTest,
        but more efficient because the test statistic is not recomputed
        """
        assert(mask.size) == sar_list[0].size
        r = Omnibus.__new__(Omnibus)
        r.sar_list = [X.masked_region(mask) for X in self.sar_list]
        r.ENL = self.ENL
        r.f = self.f
        r.rho = self.rho
        r.w2 = self.w2

        r.lnq = self.lnq[mask]
        return r

if __name__ == "__main__":
    print("Omnibus test...")

    # Omnibus test of the entire image
    omnibus = Omnibus(sar_list, 13)

    # Omnibus test over the no change region
    omnibus_no_change = Omnibus(sar_list_nochange, 13)

    # Histogram over the no change region
    fig, ax = omnibus_no_change.histogram()
    hist_filename = "fig/omnibus/hist.nochange.pdf"
    fig.savefig(hist_filename, bbox_inches='tight')

    # Histogram, entire region
    fig, ax = omnibus.histogram()
    hist_filename = "fig/omnibus/hist.total.pdf"
    fig.savefig(hist_filename, bbox_inches='tight')

    # Binary images
    def omnibus_binary(percent):
        im = omnibus.image_binary(percent)
        plt.imsave("fig/omnibus/omnibus.{}.jpg".format(percent), im, cmap="gray")

    omnibus_binary(0.00001)
    omnibus_binary(0.0001)
    omnibus_binary(0.001)
    omnibus_binary(0.01)
    omnibus_binary(0.05)
    omnibus_binary(0.10)

    # Pairwise test
    def average_test_for_masked_region(mask):
        print("March = April : {0:.4f}".format(Omnibus([march.masked_region(mask), april.masked_region(mask)], 13).pvalue()))
        print("April = May   : {0:.4f}".format(Omnibus([april.masked_region(mask), may.masked_region(mask)], 13).pvalue()))
        print("May   = June  : {0:.4f}".format(Omnibus([may.masked_region(mask), june.masked_region(mask)], 13).pvalue()))
        print("June  = July  : {0:.4f}".format(Omnibus([june.masked_region(mask), july.masked_region(mask)], 13).pvalue()))
        print("July  = August: {0:.4f}".format(Omnibus([july.masked_region(mask), august.masked_region(mask)], 13).pvalue()))
        print("Omnibus       : {0:.4f}".format(Omnibus([X.masked_region(mask) for X in sar_list], 13).pvalue()))

    # Omnibus test in notable regions
    print("")
    print("Forest:")
    average_test_for_masked_region(mask_forest)

    print("")
    print("Rye:")
    average_test_for_masked_region(mask_rye)

    print("")
    print("Grass:")
    average_test_for_masked_region(mask_grass)
