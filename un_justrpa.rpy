init python early hide:

    # Set up the namespace
    import os
    import os.path
    import renpy
    import renpy.loader
    import renpy.config
    import renpy.exports
    import zlib
    import unicodedata
    from renpy.compat.pickle import loads
    import sys
    import base64
    import pickle

    global archives
    archives=[]
    archive_handlers = [ ]


    class RPAv3ArchiveHandler(object):
        """
        Archive handler handling RPAv3 archives.
        """

        @staticmethod
        def get_supported_extensions():
            return [ ".rpa" ]

        @staticmethod
        def get_supported_headers():
            return [ b"RPA-3.0 " ]

        @staticmethod
        def read_index(infile):
            l = infile.read(40)
            offset = int(l[8:24], 16)
            key = int(l[25:33], 16)
            infile.seek(offset)
            index = loads(zlib.decompress(infile.read()))

            # Deobfuscate the index.

            for k in index.keys():

                if len(index[k][0]) == 2:
                    index[k] = [ (offset ^ key, dlen ^ key) for dlen, offset in index[k] ]
                else:
                    index[k] = [ (offset ^ key, dlen ^ key, start) for dlen, offset, start in index[k] ]
            return index


    archive_handlers.append(RPAv3ArchiveHandler)


    class RPAv2ArchiveHandler(object):
        """
        Archive handler handling RPAv2 archives.
        """

        @staticmethod
        def get_supported_extensions():
            return [ ".rpa" ]

        @staticmethod
        def get_supported_headers():
            return [ b"RPA-2.0 " ]

        @staticmethod
        def read_index(infile):
            l = infile.read(24)
            offset = int(l[8:], 16)
            infile.seek(offset)
            index = loads(zlib.decompress(infile.read()))

            return index


    archive_handlers.append(RPAv2ArchiveHandler)


    class RPAv1ArchiveHandler(object):
        """
        Archive handler handling RPAv1 archives.
        """

        @staticmethod
        def get_supported_extensions():
            return [ ".rpi" ]

        @staticmethod
        def get_supported_headers():
            return [ b"\x78\x9c" ]

        @staticmethod
        def read_index(infile):
            return loads(zlib.decompress(infile.read()))


    archive_handlers.append(RPAv1ArchiveHandler)

    def index_archives():

        global archives

        max_header_length = 0
        for handler in archive_handlers:
            for header in handler.get_supported_headers():
                header_len = len(header)
                if header_len > max_header_length:
                    max_header_length = header_len

        archive_extensions = [ ]
        for handler in archive_handlers:
            for ext in handler.get_supported_extensions():
                if not (ext in archive_extensions):
                    archive_extensions.append(ext)
        
        

        for prefix in renpy.config.archives:
            for ext in archive_extensions:
                fn = None
                f = None
                try:
                    fn = renpy.loader.transfn(prefix + ext)
                    f = open(fn, "rb")
                except:
                    continue
                with f:
                    file_header = f.read(max_header_length)
                    for handler in archive_handlers:
                        try:
                            archive_handled = False
                            for header in handler.get_supported_headers():
                                if file_header.startswith(header):
                                    f.seek(0, 0)
                                    index = handler.read_index(f)
                                    archives.append((prefix + ext, index))
                                    archive_handled = True
                                    break
                            if archive_handled == True:
                                break
                        except:
                            raise
    
    index_archives()


    basepath = os.path.join(os.getcwd(), "game")
    for prefix, index in archives:
        for fd in index:
            pa = os.path.join(basepath, fd)
            di = os.path.dirname(pa)
            if not os.path.exists(di):
                os.makedirs(di)
            with open(os.path.join(basepath, fd), "wb") as t:
                f=renpy.loader.load_from_archive(fd)
                if type(f) == renpy.loader.SubFile:
                    t.write(f.read())
                else:
                    t.write(f.getvalue())
    import atexit 
    @atexit.register 
    def clean(bpath = basepath): 
        for p in os.listdir(bpath):
            pa = os.path.join(bpath, p)
            if os.path.isdir(pa):
                clean(pa)
            else:
                f=os.path.splitext(p)
                if f[1]==".rpa":
                    os.remove(pa)

    