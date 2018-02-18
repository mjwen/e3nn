# pylint: disable=C,R,E1101
import torch
from se3_cnn import SE3BNConvolution, SE3ConvolutionBN
from se3_cnn.non_linearities import ScalarActivation
from se3_cnn.non_linearities import TensorProduct
from se3_cnn import SO3


class TensorProductBlock(torch.nn.Module):
    def __init__(self, repr_in, repr_out, size, n_radial, activation=None, stride=1, padding=0, central_base=True, overlap_threshold=-1, batch_norm_momentum=0.1, batch_norm_mode='normal', batch_norm_before_conv=True):
        super().__init__()
        self.tensor = TensorProduct([(repr_in[0], 1, False), (repr_in[1], 3, True), (repr_in[2], 5, False)]) if repr_in[1] > 0 else None
        self.bn_conv = (SE3BNConvolution if batch_norm_before_conv else SE3ConvolutionBN)(
            size=size,
            n_radial=n_radial,
            Rs_in=[(repr_in[0], SO3.repr1), (repr_in[1], SO3.repr3), (repr_in[2], SO3.repr5), (repr_in[1], SO3.repr3x3)],
            Rs_out=[(repr_out[0], SO3.repr1), (repr_out[1], SO3.repr3), (repr_out[2], SO3.repr5)],
            stride=stride,
            padding=padding,
            central_base=central_base,
            overlap_threshold=overlap_threshold,
            momentum=batch_norm_momentum,
            mode=batch_norm_mode)

        if activation is not None:
            self.act = ScalarActivation([(repr_out[0], True), (repr_out[1] * 3, False), (repr_out[2] * 5, False)], activation)
        else:
            self.act = None

    def forward(self, sv5):  # pylint: disable=W
        if self.tensor is not None:
            t = self.tensor(sv5)
            sv5t = torch.cat([sv5, t], dim=1)
        else:
            sv5t = sv5

        sv5 = self.bn_conv(sv5t)

        if self.act is not None:
            sv5 = self.act(sv5)
        return sv5