# -*- coding: utf-8 -*-
import sys
import os.path
pkgdir = os.path.dirname(__file__)

dirs = [pkgdir, os.path.join(pkgdir, ".."), os.path.join(pkgdir, "..", "..")]
for d in iter(dirs):
    d = os.path.abspath(d)
    if d not in sys.path:
        sys.path.append(os.path.join(d))
