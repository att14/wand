""":mod:`wand.api` --- Low-level interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionchanged:: 0.1.10
   Changed to throw :exc:`~exceptions.ImportError` instead of
   :exc:`~exceptions.AttributeError` when the shared library fails to load.

"""
import ctypes
import ctypes.util
import os
import os.path
import sys
import platform

__all__ = ('MagickPixelPacket', 'c_magick_char_p', 'library', 'libc',
           'libmagick', 'load_library')


class c_magick_char_p(ctypes.c_char_p):
    """This subclass prevents the automatic conversion behavior of
    :class:`ctypes.c_char_p`, allowing memory to be properly freed in the
    destructor.  It must only be used for non-const character pointers
    returned by ImageMagick functions.

    """

    def __del__(self):
        """Relinquishes memory allocated by ImageMagick.
        We don't need to worry about checking for ``NULL`` because
        :c:func:`MagickRelinquishMemory` does that for us.
        Note alslo that :class:`ctypes.c_char_p` has no
        :meth:`~object.__del__` method, so we don't need to
        (and indeed can't) call the superclass destructor.

        """
        library.MagickRelinquishMemory(self)


def load_library():
    """Loads the MagickWand library.

    :returns: the MagickWand library and the ImageMagick library

    """
    libpath = None
    system = platform.system()

    magick_home = os.environ.get('MAGICK_HOME')
    if magick_home:
        if system == 'Windows':
            libpath = 'CORE_RL_wand_.dll',
        elif system == 'Darwin':
            libpath = 'lib', 'libMagickWand.dylib',
        else:
            libpath = 'lib', 'libMagickWand.so',
        libpath = os.path.join(magick_home, *libpath)
    else:
        if system == 'Windows':
            libpath = ctypes.util.find_library('CORE_RL_wand_')
        else:
            libpath = ctypes.util.find_library('MagickWand')
    libwand = ctypes.CDLL(libpath)

    if system == 'Windows':
        # On Windows, the API is split between two libs. On other platforms,
        # it's all contained in one.
        libmagick_filename = 'CORE_RL_magick_'
        if magick_home:
            libmagick_path = os.path.join(magick_home,
                                          libmagick_filename + '.dll')
        else:
            libmagick_path = ctypes.util.find_library(libmagick_filename)
        libmagick = ctypes.CDLL(libmagick_path)
        return libwand, libmagick

    return libwand, libwand


if not hasattr(ctypes, 'c_ssize_t'):
    if ctypes.sizeof(ctypes.c_uint) == ctypes.sizeof(ctypes.c_void_p):
        ctypes.c_ssize_t = ctypes.c_int
    elif ctypes.sizeof(ctypes.c_ulong) == ctypes.sizeof(ctypes.c_void_p):
        ctypes.c_ssize_t = ctypes.c_long
    elif ctypes.sizeof(ctypes.c_ulonglong) == ctypes.sizeof(ctypes.c_void_p):
        ctypes.c_ssize_t = ctypes.c_longlong


class MagickPixelPacket(ctypes.Structure):

    _fields_ = [('storage_class', ctypes.c_int),
                ('colorspace', ctypes.c_int),
                ('matte', ctypes.c_int),
                ('fuzz', ctypes.c_double),
                ('depth', ctypes.c_size_t),
                ('red', ctypes.c_double),
                ('green', ctypes.c_double),
                ('blue', ctypes.c_double),
                ('opacity', ctypes.c_double),
                ('index', ctypes.c_double)]


try:
    libraries = load_library()
except (OSError, IOError):
    msg = 'http://dahlia.github.com/wand/guide/install.html'
    if sys.platform.startswith('freebsd'):
        msg = 'pkg_add -r'
    elif sys.platform == 'win32':
        msg += '#install-imagemagick-on-windows'
    elif sys.platform == 'darwin':
        for pkgmgr in 'brew', 'port':
            with os.popen('which ' + pkgmgr) as f:
                if f.read().strip():
                    msg = pkgmgr + ' install imagemagick'
                    break
        else:
            msg += '#install-imagemagick-on-mac'
    else:
        distname, _, __ = platform.linux_distribution()
        distname = (distname or '').lower()
        if distname in ('debian', 'ubuntu'):
            msg = 'apt-get install libmagickwand-dev'
        elif distname in ('fedora', 'centos', 'redhat'):
            msg = 'yum install ImageMagick-devel'
    raise ImportError('MagickWand shared library not found.\n'
                      'You probably had not installed ImageMagick library.\n'
                      'Try to install:\n  ' + msg)

#: (:class:`ctypes.CDLL`) The MagickWand library.
library = libraries[0]

#: (:class:`ctypes.CDLL`) The ImageMagick library.  It is the same with
#: :data:`library` on platforms other than Windows.
#:
#: .. versionadded:: 0.1.10
libmagick = libraries[1]

try:
    library.MagickWandGenesis.argtypes = []
    library.MagickWandTerminus.argtypes = []

    library.NewMagickWand.argtypes = []
    library.NewMagickWand.restype = ctypes.c_void_p

    library.MagickNewImage.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                       ctypes.c_int, ctypes.c_void_p]

    library.ClearMagickWand.argtypes = [ctypes.c_void_p]

    library.DestroyMagickWand.argtypes = [ctypes.c_void_p]
    library.DestroyMagickWand.restype = ctypes.c_void_p

    library.CloneMagickWand.argtypes = [ctypes.c_void_p]
    library.CloneMagickWand.restype = ctypes.c_void_p

    library.IsMagickWand.argtypes = [ctypes.c_void_p]

    library.MagickGetException.argtypes = [ctypes.c_void_p,
                                           ctypes.POINTER(ctypes.c_int)]
    library.MagickGetException.restype = c_magick_char_p

    library.MagickClearException.argtypes = [ctypes.c_void_p]

    library.MagickSetFilename.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    library.MagickReadImageBlob.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_size_t]

    library.MagickReadImage.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    library.MagickReadImageFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    library.MagickGetImageFormat.argtypes = [ctypes.c_void_p]
    library.MagickGetImageFormat.restype = c_magick_char_p

    library.MagickSetImageFormat.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    libmagick.MagickToMime.argtypes = [ctypes.c_char_p]
    libmagick.MagickToMime.restype = c_magick_char_p

    library.MagickGetImageSignature.argtypes = [ctypes.c_void_p]
    library.MagickGetImageSignature.restype = c_magick_char_p

    library.MagickGetImageProperty.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    library.MagickGetImageProperty.restype = c_magick_char_p

    library.MagickGetImageProperties.argtypes = [ctypes.c_void_p,
                                                 ctypes.c_char_p,
                                                 ctypes.POINTER(ctypes.c_size_t)]
    library.MagickGetImageProperties.restype = ctypes.POINTER(ctypes.c_char_p)

    library.MagickSetImageProperty.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                               ctypes.c_char_p]

    library.MagickDeleteImageProperty.argtypes = [ctypes.c_void_p,
                                                  ctypes.c_char_p]
    library.MagickGetImageBackgroundColor.argtypes = [ctypes.c_void_p,
                                                      ctypes.c_void_p]

    library.MagickSetImageBackgroundColor.argtypes = [ctypes.c_void_p,
                                                      ctypes.c_void_p]

    library.MagickGetImageAlphaChannel.argtypes = [ctypes.c_void_p]
    library.MagickGetImageAlphaChannel.restype = ctypes.c_size_t

    library.MagickSetImageAlphaChannel.argtypes = [ctypes.c_void_p,
                                                   ctypes.c_int]

    library.MagickGetImageBlob.argtypes = [ctypes.c_void_p,
                                           ctypes.POINTER(ctypes.c_size_t)]
    library.MagickGetImageBlob.restype = ctypes.POINTER(ctypes.c_ubyte)

    library.MagickWriteImage.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    library.MagickWriteImageFile.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    library.MagickGetImageResolution.argtypes = [ctypes.c_void_p,
                  ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]

    library.MagickSetImageResolution.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
    library.MagickSetResolution.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]

    library.MagickGetImageWidth.argtypes = [ctypes.c_void_p]
    library.MagickGetImageWidth.restype = ctypes.c_size_t

    library.MagickGetImageHeight.argtypes = [ctypes.c_void_p]
    library.MagickGetImageHeight.restype = ctypes.c_size_t

    library.MagickGetImageUnits.argtypes = [ctypes.c_void_p]

    library.MagickSetImageUnits.argtypes = [ctypes.c_void_p, ctypes.c_int]

    library.MagickGetImageDepth.argtypes = [ctypes.c_void_p]
    library.MagickGetImageDepth.restype = ctypes.c_size_t

    library.MagickSetImageDepth.argtypes = [ctypes.c_void_p]

    library.MagickGetImageChannelDepth.argtypes = [ctypes.c_void_p,
                                                   ctypes.c_int]
    library.MagickGetImageChannelDepth.restype = ctypes.c_size_t

    library.MagickSeparateImageChannel.argtypes = [ctypes.c_void_p,
                                                   ctypes.c_int]

    library.MagickCropImage.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                        ctypes.c_size_t, ctypes.c_ssize_t,
                                        ctypes.c_ssize_t]

    library.MagickResetImagePage.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    library.MagickResizeImage.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                          ctypes.c_size_t, ctypes.c_int,
                                          ctypes.c_double]

    library.MagickTransformImage.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                             ctypes.c_char_p]
    library.MagickTransformImage.restype = ctypes.c_void_p

    library.MagickRotateImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_double]

    library.MagickResetIterator.argtypes = [ctypes.c_void_p]

    library.MagickIdentifyImage.argtypes = [ctypes.c_void_p]
    library.MagickIdentifyImage.restype = ctypes.c_char_p

    library.MagickRelinquishMemory.argtypes = [ctypes.c_void_p]
    library.MagickRelinquishMemory.restype = ctypes.c_void_p

    library.NewPixelIterator.argtypes = [ctypes.c_void_p]
    library.NewPixelIterator.restype = ctypes.c_void_p

    library.DestroyPixelIterator.argtypes = [ctypes.c_void_p]
    library.DestroyPixelIterator.restype = ctypes.c_void_p

    library.ClonePixelIterator.argtypes = [ctypes.c_void_p]
    library.ClonePixelIterator.restype = ctypes.c_void_p

    library.IsPixelIterator.argtypes = [ctypes.c_void_p]

    library.PixelGetIteratorException.argtypes = [ctypes.c_void_p,
                                                  ctypes.POINTER(ctypes.c_int)]
    library.PixelGetIteratorException.restype = c_magick_char_p

    library.PixelClearIteratorException.argtypes = [ctypes.c_void_p]

    library.PixelSetFirstIteratorRow.argtypes = [ctypes.c_void_p]

    library.PixelSetIteratorRow.argtypes = [ctypes.c_void_p, ctypes.c_ssize_t]

    library.PixelGetNextIteratorRow.argtypes = [ctypes.c_void_p,
                                                ctypes.POINTER(ctypes.c_size_t)]
    library.PixelGetNextIteratorRow.restype = ctypes.POINTER(ctypes.c_void_p)

    library.NewPixelWand.restype = ctypes.c_void_p

    library.DestroyPixelWand.argtypes = [ctypes.c_void_p]
    library.DestroyPixelWand.restype = ctypes.c_void_p

    library.IsPixelWand.argtypes = [ctypes.c_void_p]

    library.PixelGetException.argtypes = [ctypes.c_void_p,
                                          ctypes.POINTER(ctypes.c_int)]
    library.PixelGetException.restype = c_magick_char_p

    library.PixelClearException.argtypes = [ctypes.c_void_p]

    library.IsPixelWandSimilar.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                           ctypes.c_double]

    library.PixelGetMagickColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    library.PixelSetMagickColor.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    library.PixelSetColor.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    library.PixelGetColorAsString.argtypes = [ctypes.c_void_p]
    library.PixelGetColorAsString.restype = c_magick_char_p

    library.PixelGetAlpha.argtypes = [ctypes.c_void_p]
    library.PixelGetAlpha.restype = ctypes.c_double

    library.MagickGetQuantumRange.argtypes = [ctypes.POINTER(ctypes.c_size_t)]

    library.MagickSetIteratorIndex.argtypes = [ctypes.c_void_p,
                                               ctypes.c_ssize_t]

    library.MagickGetImageType.argtypes = [ctypes.c_void_p]

    library.MagickSetImageType.argtypes = [ctypes.c_void_p, ctypes.c_int]

    library.MagickEvaluateImageChannel.argtypes = [ctypes.c_void_p,
                                                   ctypes.c_int,
                                                   ctypes.c_int,
                                                   ctypes.c_double]

    library.MagickCompositeImage.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_int, ctypes.c_ssize_t,
                                             ctypes.c_ssize_t]

    library.MagickGetImageCompressionQuality.argtypes = [ctypes.c_void_p]
    library.MagickGetImageCompressionQuality.restype = ctypes.c_ssize_t

    library.MagickSetImageCompressionQuality.argtypes = [ctypes.c_void_p,
                                                         ctypes.c_ssize_t]

    library.MagickStripImage.argtypes = [ctypes.c_void_p]

    library.MagickTrimImage.argtypes = [ctypes.c_void_p]

    # These functions are const so it's okay for them to be c_char_p
    libmagick.GetMagickVersion.argtypes = [ctypes.POINTER(ctypes.c_size_t)]
    libmagick.GetMagickVersion.restype = ctypes.c_char_p

    libmagick.GetMagickReleaseDate.argtypes = []
    libmagick.GetMagickReleaseDate.restype = ctypes.c_char_p
except AttributeError:
    raise ImportError('MagickWand shared library not found or incompatible')

#: (:class:`ctypes.CDLL`) The C standard library.
libc = None

if platform.system() == 'Windows':
    libc = ctypes.CDLL(ctypes.util.find_msvcrt())
else:
    if platform.system() == 'Darwin':
        libc = ctypes.cdll.LoadLibrary('libc.dylib')
    elif platform.system() == 'FreeBSD':
        libc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
    else:
        libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.fdopen.argtypes = [ctypes.c_int, ctypes.c_char_p]
    libc.fdopen.restype = ctypes.c_void_p

libc.free.argtypes = [ctypes.c_void_p]

