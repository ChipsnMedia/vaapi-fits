###
### Copyright (C) 2018-2019 Intel Corporation
###
### SPDX-License-Identifier: BSD-3-Clause
###

from .....lib import *
from .....lib.ffmpeg.vaapi.util import *
from .....lib.ffmpeg.vaapi.encoder import EncoderTest

spec      = load_test_spec("av1", "encode", "10bit")

@slash.requires(*have_ffmpeg_encoder("av1_vaapi"))
class AV1_10EncoderBaseTest(EncoderTest):
  def before(self):
    super().before()
    vars(self).update(
      codec   = "av1-10",
      ffenc   = "av1_vaapi",
    )

  def get_file_ext(self):
    return "ivf"

  def get_vaapi_profile(self):
    return "VAProfileAV1Profile0"

@slash.requires(*platform.have_caps("encode", "av1_10"))
class AV1_10EncoderTest(AV1_10EncoderBaseTest):
  def before(self):
    super().before()
    vars(self).update(
      caps      = platform.get_caps("encode", "av1_10"),
      lowpower  = 0,
    )

@slash.requires(*platform.have_caps("vdenc", "av1_10"))
class AV1_10EncoderLPTest(AV1_10EncoderBaseTest):
  def before(self):
    super().before()
    vars(self).update(
      caps      = platform.get_caps("vdenc", "av1_10"),
      lowpower  = 1,
    )

class cqp(AV1_10EncoderTest):
  def init(self, tspec, case, gop, slices, bframes, qp, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      bframes = bframes,
      case    = case,
      gop     = gop,
      profile = profile,
      qp      = qp,
      rcmode  = "cqp",
      slices  = slices,
    )

  @parametrize_with_unused(*gen_av1_cqp_parameters(spec, ['main']), ['quality'])
  def test(self, case, gop, slices, bframes, qp, quality, profile):
    self.init(spec, case, gop, slices, bframes, qp, profile)
    self.encode()


class cqp_lp(AV1_10EncoderLPTest):
  def init(self, tspec, case, gop, slices, qp, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      case    = case,
      gop     = gop,
      profile = profile,
      qp      = qp,
      rcmode  = "cqp",
      slices  = slices,
    )

  @parametrize_with_unused(*gen_av1_cqp_lp_parameters(spec, ['main']), ['quality'])
  def test(self, case, gop, slices, qp, quality, profile):
    self.init(spec, case, gop, slices, qp, profile)
    self.encode()

class cbr(AV1_10EncoderTest):
  def init(self, tspec, case, gop, slices, bframes, bitrate, fps, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      bframes = bframes,
      bitrate = bitrate,
      case = case,
      fps = fps,
      gop = gop,
      minrate = bitrate,
      maxrate = bitrate,
      profile = profile,
      rcmode = "cbr",
      slices = slices,
    )

  @slash.parametrize(*gen_av1_cbr_parameters(spec, ['main']))
  def test(self, case, gop, slices, bframes, bitrate, fps, profile):
    self.init(spec, case, gop, slices, bframes, bitrate, fps, profile)
    self.encode()


class cbr_lp(AV1_10EncoderLPTest):
  def init(self, tspec, case, gop, slices, bitrate, fps, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      bitrate = bitrate,
      case = case,
      fps = fps,
      gop = gop,
      minrate = bitrate,
      maxrate = bitrate,
      profile = profile,
      rcmode = "cbr",
      slices = slices,
    )

  @slash.parametrize(*gen_av1_cbr_lp_parameters(spec, ['main']))
  def test(self, case, gop, slices, bitrate, fps, profile):
    self.init(spec, case, gop, slices, bitrate, fps, profile)
    self.encode()


class vbr(AV1_10EncoderTest):
  def init(self, tspec, case, gop, slices, bframes, bitrate, fps, refs, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      bframes = bframes,
      bitrate = bitrate,
      case = case,
      fps = fps,
      gop = gop,
      maxrate = bitrate * 2, # target percentage 50%
      minrate = bitrate,
      profile = profile,
      rcmode = "vbr",
      refs = refs,
      slices = slices,
    )

  @parametrize_with_unused(*gen_av1_vbr_parameters(spec, ['main']), ['quality'])
  def test(self, case, gop, slices, bframes, bitrate, fps, quality, refs, profile):
    self.init(spec, case, gop, slices, bframes, bitrate, fps, refs, profile)
    self.encode()


class vbr_lp(AV1_10EncoderLPTest):
  def init(self, tspec, case, gop, slices, bitrate, fps, refs, profile):
    vars(self).update(tspec[case].copy())
    vars(self).update(
      bitrate = bitrate,
      case = case,
      fps = fps,
      gop = gop,
      maxrate = bitrate * 2, # target percentage 50%
      minrate = bitrate,
      profile = profile,
      rcmode = "vbr",
      refs = refs,
      slices = slices,
    )

  @parametrize_with_unused(*gen_av1_vbr_lp_parameters(spec, ['main']), ['quality'])
  def test(self, case, gop, slices, bitrate, fps, quality, refs, profile):
    self.init(spec, case, gop, slices, bitrate, fps, refs, profile)
    self.encode()

