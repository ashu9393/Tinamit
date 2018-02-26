from tinamit.MDS.Stella import ModeloStella
import os

modelo = ModeloStella(os.path.join(os.path.split(__file__)[0], 'm1.TXT'))

from pprint import pprint

pprint(modelo.niveles)