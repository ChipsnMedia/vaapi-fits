###
### Copyright (C) 2018-2019 Intel Corporation
###
### SPDX-License-Identifier: BSD-3-Clause
###

from ....lib import *
from .util import *

@slash.requires(have_ffmpeg)
@slash.requires(have_ffmpeg_vaapi_accel)
class EncoderTest(slash.Test):
  def gen_input_opts(self):
    opts = "-f rawvideo -pix_fmt {mformat} -s:v {width}x{height}"

    if vars(self).get("fps", None) is not None:
      opts += " -r:v {fps}"

    opts += " -i {source}"

    return opts

  def gen_output_opts(self):
    opts = "-vf 'format={hwformat},hwupload' -c:v {ffenc}"

    # BUG: It appears there's a ffmpeg bug with yuv420p hwupload when using
    # i965 driver.  Need to report upstream ffmpeg!

    if vars(self).get("profile", None) is not None:
      opts += " -profile:v {mprofile}"

    if self.codec not in ["jpeg",]:
      opts += " -rc_mode {rcmodeu}"

    if vars(self).get("gop", None) is not None:
      opts += " -g {gop}"
    if vars(self).get("qp", None) is not None:
      if self.codec in ["vp8", "vp9",]:
        opts += " -global_quality {qp}"
      elif self.codec in ["mpeg2"]:
        opts += " -global_quality {mqp}"
      else:
        opts += " -qp {qp}"
    if vars(self).get("quality", None) is not None:
      if self.codec in ["jpeg",]:
        opts += " -global_quality {quality}"
      else:
        opts += " -quality {quality}"
    if vars(self).get("slices", None) is not None:
      opts += " -slices {slices}"
    if vars(self).get("bframes", None) is not None:
      opts += " -bf {bframes}"
    if vars(self).get("minrate", None) is not None:
      opts += " -b:v {minrate}k"
    if vars(self).get("maxrate", None) is not None:
      opts += " -maxrate {maxrate}k"
    if vars(self).get("refmode", None) is not None:
      opts += " -refs {refs}"
    if vars(self).get("lowpower", None) is not None:
      opts += " -low_power {lowpower}"
    if vars(self).get("loopshp", None) is not None:
      opts += " -loop_filter_sharpness {loopshp}"
    if vars(self).get("looplvl", None) is not None:
      opts += " -loop_filter_level {looplvl}"
    if vars(self).get("level", None) is not None:
      self.level /= 10.0
      opts += " -level {level}"

    # WA: LDB is not enabled by default for HEVCe on gen11+, yet.
    if get_media()._get_gpu_gen() >= 11 and self.codec.startswith("hevc"):
      opts += " -b_strategy 1"

    opts += " -vframes {frames} -y {encoded}"

    return opts

  def gen_name(self):
    name = "{case}-{rcmode}"
    if vars(self).get("profile", None) is not None:
      name += "-{profile}"
    if vars(self).get("fps", None) is not None:
      name += "-{fps}"
    if vars(self).get("gop", None) is not None:
      name += "-{gop}"
    if vars(self).get("qp", None) is not None:
      name += "-{qp}"
    if vars(self).get("slices", None) is not None:
      name += "-{slices}"
    if vars(self).get("quality", None) is not None:
      name += "-{quality}"
    if vars(self).get("bframes", None) is not None:
      name += "-{bframes}"
    if vars(self).get("minrate", None) is not None:
      name += "-{minrate}k"
    if vars(self).get("maxrate", None) is not None:
      name += "-{maxrate}k"
    if vars(self).get("refmode", None) is not None:
      name += "-{refs}"
    if vars(self).get("lowpower", None) is not None:
      name += "-{lowpower}"
    if vars(self).get("loopshp", None) is not None:
      name += "-{loopshp}"
    if vars(self).get("looplvl", None) is not None:
      name += "-{looplvl}"
    if vars(self).get("r2r", None) is not None:
      name += "-r2r"
    if vars(self).get("level", None) is not None:
      name += "-{level}"

    return name

  def before(self):
    self.refctx = []
    self.renderDevice = get_media().render_device

  @timefn("ffmpeg")
  def call_ffmpeg(self, iopts, oopts):
    self.output = call(
      "ffmpeg -hwaccel vaapi -vaapi_device {renderDevice} -v verbose"
      " {iopts} {oopts}".format(renderDevice = self.renderDevice, iopts = iopts, oopts = oopts))

  def call_ffmpeg_va_stream(self, iopts, oopts):
      stream_name = self.encoded
      try:
          file_name = os.path.basename(stream_name)
          file_dir = os.path.dirname(stream_name)
          if os.path.isdir(file_dir) == False:
              os.mkdir(file_dir)
          ivf_file_dir = self.cnm_refc_dir + "/ivf"
          if os.path.isdir(ivf_file_dir) == False:
              os.mkdir(ivf_file_dir)
      except Exception as e:
          print("Exception str=" + str(e))
          pass
      self.va_stream_name = ivf_file_dir + "/" + file_name + ".ivf" 
      self.va_yuv_name = ivf_file_dir + "/" + file_name + ".enc.yuv" 
      MY_LIBVA_DRIVERS_PATH = "/usr/lib/x86_64-linux-gnu/dri"
      MY_LIBVA_DRIVER_NAME = "iHD"
      os.putenv("LIBVA_DRIVERS_PATH", MY_LIBVA_DRIVERS_PATH)
      os.putenv("LIBVA_DRIVER_NAME", MY_LIBVA_DRIVER_NAME)
      os.putenv("LIBVA_TRACE", "libva_trace_file")
      os.putenv("LIBVA_VA_BITSTREAM", self.va_stream_name)
      os.putenv("LIBVA_TRACE_SURFACE", self.va_yuv_name)
      os.system("echo $LIBVA_VA_BITSTREAM")
      os.system("echo $LIBVA_TRACE_SURFACE")
      cmd_str = "ffmpeg -hwaccel vaapi -vaapi_device {renderDevice} -v verbose {iopts} {oopts}".format(renderDevice = self.renderDevice, iopts = iopts, oopts = oopts)
      print("run ffmpeg for va stream : " + cmd_str)
      try:
        self.output = call(cmd_str)
          # if os.system(cmd_str) == 0:
          #     ret = True
      except Exception as e:
          print("Exception str=" + str(e))
          pass

  def validate_caps(self):
    # BUG: FFmpeg fails to support I420 hwupload even though i965 supports it.
    ifmts = list(set(self.caps["fmts"]) - set(["I420"]))
    self.hwformat = map_best_hw_format(self.format, ifmts)
    self.mformat = mapformat(self.format)
    if None in [self.hwformat, self.mformat]:
      slash.skip_test("{format} not supported".format(**vars(self)))

    skip_test_if_missing_features(self)

    maxw, maxh = self.caps["maxres"]
    if self.width > maxw or self.height > maxh:
      slash.skip_test(
        format_value(
          "{platform}.{driver}.{width}x{height} not supported", **vars(self)))

    if vars(self).get("slices", 1) > 1 and not self.caps.get("multislice", True):
      slash.skip_test(
        format_value(
          "{platform}.{driver}.slice > 1 unsupported in this mode", **vars(self)))

    if not self.caps.get(self.rcmode, True):
      slash.skip_test(
        format_value(
          "{platform}.{driver}.{rcmode} unsupported in this mode", **vars(self)))

    if vars(self).get("profile", None) is not None:
      self.mprofile = mapprofile(self.codec, self.profile)
      if self.mprofile is None:
        slash.skip_test("{profile} profile is not supported".format(**vars(self)))

    vars(self).update(rcmodeu = self.rcmode.upper())

  def encode(self):
    self.validate_caps()

    iopts = self.gen_input_opts()
    oopts = self.gen_output_opts()
    name  = self.gen_name().format(**vars(self))
    ext   = self.get_file_ext()

    self.encoded = get_media()._test_artifact("{}.{}".format(name, ext))

    self.cnm_refc_dir = get_media()._get_cnm_refc_dir()
    if self.cnm_refc_dir is not None and self.cnm_refc_dir != '':
      # call ffmpeg for ivf generation
      self.call_ffmpeg_va_stream(iopts.format(**vars(self)), oopts.format(**vars(self)))
      # convert self.source NV12 to yuv420p
      cmd_str = "ffmpeg -pix_fmt " + str(self.mformat) + " -s:v " + str(self.width) + "x" + str(self.height) + " -i " + str(self.va_yuv_name) + " -vframes " + str(self.frames) + " -c:v rawvideo -pix_fmt yuv420p " + str(self.va_yuv_name) + ".yuv420p.yuv -y"
      try:
        if os.system(cmd_str) == 0:
            ret = True
      except Exception as e:
          print("Exception str=" + str(e))
          pass
      # make cmodel cfg
      file_name = os.path.basename(self.encoded)
      refc_outputFile = self.cnm_refc_dir + "/" + file_name
      refc_cfgFile = self.cnm_refc_dir + "/" + file_name + ".vaenc.cfg"
      refc_inputFile = str(self.va_yuv_name) + ".yuv420p.yuv"

      f = open(refc_cfgFile, "w")
      f.write("# CONFIG" + " \t\r\n")
      f.write("#-------------------------------" + " \t\r\n")
      f.write("InputFile                :        " + refc_inputFile + " \t\r\n")
      f.write("FramesToBeEncoded        :        " + str(self.frames) + " \t\r\n") 
      f.write("CodecStd                 :        3" + " \t\r\n")
      f.write("NoLastFrameCheck         :        1" + " \t\r\n")
      f.write("SourceWidth              :        " + str(self.width) + " \t\r\n")
      f.write("SourceHeight             :        " + str(self.height) + " \t\r\n")
      f.write("InputBitDepth            :        8  \t\r\n")      
      if "cbr" == self.rcmode:
        f.write("RateControl             :        2  \t\r\n")      
      elif "vbr" == self.rcmode:
        f.write("RateControl             :        1  \t\r\n")      
      else:
        f.write("RateControl             :        0  \t\r\n")      
      f.close()
      os.system("cat " + refc_cfgFile)
      # make cmodel command 
      cmd_str = self.cnm_refc_dir + "/Gaudi -i " + refc_cfgFile + " -o " + refc_outputFile + " -v " + str(self.va_stream_name) 
      print("run ref-c : " + cmd_str)
      try:
        if os.system(cmd_str) == 0:
            ret = True
      except Exception as e:
          print("Exception str=" + str(e))
          pass
      cmd_str = "cp -f " + refc_outputFile + " " + self.encoded
      print("copy encoded file for ref-c: " + cmd_str)
      try:
        if os.system(cmd_str) == 0:
            ret = True
      except Exception as e:
          print("Exception str=" + str(e))
          pass
    else:
        self.call_ffmpeg(iopts.format(**vars(self)), oopts.format(**vars(self)))

    if vars(self).get("r2r", None) is not None:
      assert type(self.r2r) is int and self.r2r > 1, "invalid r2r value"
      md5ref = md5(self.encoded)
      get_media()._set_test_details(md5_ref = md5ref)
      for i in range(1, self.r2r):
        self.encoded = get_media()._test_artifact("{}_{}.{}".format(name, i, ext))
        self.call_ffmpeg(iopts.format(**vars(self)), oopts.format(**vars(self)))
        result = md5(self.encoded)
        get_media()._set_test_details(**{"md5_{:03}".format(i) : result})
        assert result == md5ref, "r2r md5 mismatch"
        # delete encoded file after each iteration
        get_media()._purge_test_artifact(self.encoded)
    else:
      self.check_output()
      self.check_bitrate()
      self.check_metrics()

  def check_output(self):
    # profile
    m = re.search(
      "Using VAAPI profile {} ([0-9]*)".format(self.get_vaapi_profile()),
      self.output, re.MULTILINE)
    assert m is not None, "Possible incorrect profile used"

    # entrypoint
    entrypointmsgs = [
      "Using VAAPI entrypoint {} ([0-9]*)".format(
        "VAEntrypointEncSlice" if "jpeg" != self.codec else "VAEntrypointEncPicture"),
      "Using VAAPI entrypoint VAEntrypointEncSliceLP ([0-9]*)",
    ]
    m = re.search(
      entrypointmsgs[vars(self).get("lowpower", 0)], self.output, re.MULTILINE)
    assert m is not None, "Possible incorrect entrypoint used"

    # rate control mode
    rcmsgs = dict(
      cqp = (
        "Using constant-quality mode"
        "|RC mode: CQP"
        "|Driver does not report any supported rate control modes: assuming constant-quality"
      ),
      cbr = "RC mode: CBR",
      vbr = "RC mode: VBR",
    )
    m = re.search(rcmsgs[self.rcmode], self.output, re.MULTILINE)
    assert m is not None, "Possible incorrect RC mode used"

    # ipb mode
    ipbmode = 0 if vars(self).get("gop", 0) <= 1 else 1 if vars(self).get("bframes", 0) < 1 else 2
    ipbmsgs = [
      "Using intra frames only",
      "Using intra and P-frames|[L|l]ow delay|forward-prediction",
      "Using intra, P- and B-frames|[L|l]ow delay|forward-prediction",
    ]
    m = re.search(ipbmsgs[ipbmode], self.output, re.MULTILINE)
    assert m is not None, "Possible incorrect IPB mode used"

    if vars(self).get("level", None) is not None:
      self.check_level()

  def check_metrics(self):
    iopts = "-i {encoded}"
    oopts = (
      "-pix_fmt {mformat} -f rawvideo -vsync passthrough"
      " -vframes {frames} -y {decoded}")
    name = (self.gen_name() + "-{width}x{height}-{format}").format(**vars(self))
    self.decoded = get_media()._test_artifact("{}.yuv".format(name))
    self.call_ffmpeg(iopts.format(**vars(self)), oopts.format(**vars(self)))

    get_media().baseline.check_psnr(
      psnr = calculate_psnr(
        self.source, self.decoded,
        self.width, self.height,
        self.frames, self.format),
      context = self.refctx,
    )

  def check_bitrate(self):
    encsize = os.path.getsize(self.encoded)
    bitrate_actual = encsize * 8 * vars(self).get("fps", 25) / 1024.0 / self.frames
    get_media()._set_test_details(
      size_encoded = encsize,
      bitrate_actual = "{:-.2f}".format(bitrate_actual))

    if "cbr" == self.rcmode:
      bitrate_gap = abs(bitrate_actual - self.bitrate) / self.bitrate
      get_media()._set_test_details(bitrate_gap = "{:.2%}".format(bitrate_gap))

      # acceptable bitrate within 10% of bitrate
      assert(bitrate_gap <= 0.10)

    elif "vbr" == self.rcmode:
      # acceptable bitrate within 25% of minrate and 10% of maxrate
      assert(self.minrate * 0.75 <= bitrate_actual <= self.maxrate * 1.10)

  def check_level(self):
    output = call(
      "ffprobe -i {encoded} -v quiet -show_entries stream=level"
      " -of default=nk=1:nw=1".format(**vars(self)))
    assert float(output)/30 == self.level, "fail to set target level"
