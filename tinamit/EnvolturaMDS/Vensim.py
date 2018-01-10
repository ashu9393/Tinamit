import ctypes
import re
import struct
import sys
from warnings import warn as avisar

import numpy as np

from tinamit.MDS import EnvolturaMDS
from ._sintaxis import sacar_arg, sacar_variables, juntar_líns, cortar_líns

if sys.platform[:3] == 'win':
    try:
        ctypes.WinDLL('C:\\Windows\\System32\\vendll32.dll')
        dll_Vensim = 'C:\\Windows\\System32\\vendll32.dll'
    except OSError:
        try:
            ctypes.WinDLL('C:\\Windows\\SysWOW64\\vendll32.dll')
            dll_Vensim = 'C:\\Windows\\SysWOW64\\vendll32.dll'
        except OSError:
            dll_Vensim = None
            avisar('Esta computadora no tiene el DLL de Vensim DSS. Las funciones con modelos Vensim se verán'
                   'limitados.')


class ModeloVensimMdl(EnvolturaMDS):

    def inic_vars(símismo):

        doc = símismo.archivo

        # Borrar lo que podría haber allí desde antes.
        símismo.variables.clear()
        símismo.dic_doc.clear()

        # Variables internos a VENSIM
        símismo.internos = ['FINAL TIME', 'TIME STEP', 'INITIAL TIME', 'SAVEPER', 'Time']

        # La primera línea del documento, con {UTF-8}
        símismo.dic_doc['cabeza'] = doc[0]

        # La primera línea con informacion de variables
        prim_vars = 1

        # La primer línea que NO contiene información de variables ("****...***" para VENSIM).
        fin_vars = next((n for n, l in enumerate(doc) if re.match(r'\*+$', l)), None)

        # La región con información de variables
        sec_vars = doc[prim_vars:fin_vars]

        # Una lista de tuples que indican dónde empieza y termina cada variable
        índs_vars = [(n, (n + 1) + next(i for i, l_v in enumerate(sec_vars[n + 1:]) if re.match('\n', l_v)))
                     for n, l in enumerate(sec_vars) if re.match(r'[\w]|\"', l)]

        # Guardar todo el resto del archivo (que no contiene información de ecuaciones de variables).
        símismo.dic_doc['cola'] = doc[fin_vars:]

        for ubic_var in índs_vars:
            # Extraer la información del variable
            nombre, dic_var = símismo._leer_var(l_texto=sec_vars[ubic_var[0]:ubic_var[1]])

            símismo.vars[nombre] = dic_var

        # Transferir los nombres de los variables parientes a los diccionarios de sus hijos correspondientes
        for var, d_var in símismo.vars.items():
            for pariente in d_var['parientes']:
                símismo.vars[pariente]['hijos'].append(var)

        # Borrar lo que había antes en las listas siguientes:
        símismo.flujos.clear()
        símismo.auxiliares.clear()
        símismo.constantes.clear()
        símismo.niveles.clear()

        # Guardar una lista de los nombres de variables de tipo "nivel"
        símismo.niveles += [x for x in símismo.vars if re.match(r'INTEG *\(', símismo.vars[x]['ec']) is not None]

        # Los flujos, por definición, son los parientes de los niveles.
        for niv in símismo.niveles:

            # El primer argumento de la función INTEG de VENSIM
            arg_integ = sacar_arg(símismo.vars[niv]['ec'], regex_var=símismo.regex_var,
                                  regex_fun=símismo.regex_fun, i=0)

            # Extraer los variables flujos
            flujos = sacar_variables(arg_integ, regex=símismo.regex_var, excluir=símismo.internos)

            for flujo in flujos:
                # Para cada nivel en el modelo...

                if flujo not in símismo.flujos:
                    # Agregar el flujo, si no está ya en la lista de flujos.

                    símismo.flujos.append(flujo)

        # Los auxiliares son los variables con parientes que son ni niveles, ni flujos.
        símismo.auxiliares += [x for x, d in símismo.vars.items()
                               if x not in símismo.niveles and x not in símismo.flujos
                               and len(d['parientes'])]

        # Los constantes son los variables que quedan.
        símismo.constantes += [x for x in símismo.vars if x not in símismo.niveles and x not in símismo.flujos
                               and x not in símismo.auxiliares]

    def _leer_var(símismo, l_texto):
        """
        Esta función toma un lista de las líneas de texto que especifican un variable y le extrae su información.

        :param l_texto: Una lista del texto que corresponde a este variable.
        :type l_texto: list

        :return: El numbre del variable, y un diccionario con su información
        :rtype: (str, dict)
        """

        # Identificar el nombre del variable
        nombre = sacar_variables(l_texto[0], rgx=símismo.regex_var, n=1)[0]

        # El diccionario en el cual guardar todo
        dic_var = {'nombre': nombre, 'unidades': '', 'comentarios': '', 'hijos': [], 'parientes': [], 'ec': ''}

        # Sacar el inicio de la ecuación que puede empezar después del signo de igualdad.
        m = re.match(r' *=(.*)$', l_texto[0][len(nombre):])
        if m is None:
            princ_ec = ''
        else:
            princ_ec = m.groups()[0]

        # El principio de las unidades
        prim_unid = next(n for n, l in enumerate(l_texto) if re.match(r'\t~\t', l))

        # El principio de los comentarios
        prim_com = next(n + (prim_unid + 1) for n, l in enumerate(l_texto[prim_unid + 1:]) if re.match(r'\t~\t', l))

        # Combinar las líneas de texto de la ecuación
        ec = juntar_líns([princ_ec] + l_texto[1:prim_unid])

        # Extraer los nombre de los variables parientes
        dic_var['parientes'] = sacar_variables(texto=ec, rgx=símismo.regex_var, excluir=símismo.internos)

        # Si no hay ecuación especificada, dar una ecuación vacía.
        if re.match(r'A FUNCTION OF *\(', ec) is not None:
            dic_var['ec'] = ''
        else:
            dic_var['ec'] = ec

        # Ahora sacamos las unidades.
        dic_var['unidades'] = juntar_líns(l_texto[prim_unid:prim_com], cabeza=r'\t~?\t')

        # Y ahora agregamos todas las líneas que quedan para la sección de comentarios
        dic_var['comentarios'] = juntar_líns(l_texto[prim_com:], cabeza=r'\t~?\t', cola=r'\t\|')

        # Devolver el variable decifrado.
        return nombre, dic_var

    def _escribir_var(símismo, var):
        """

        :param var:
        :type var: str

        :return:
        :rtype: str
        """

        dic_var = símismo.var[var]

        if dic_var['ec'] == '':
            dic_var['ec'] = 'A FUNCTION OF (%s)' % ', '.join(dic_var['parientes'])

        texto = [var + '=\n',
                 cortar_líns(dic_var['ec'], símismo.lím_línea, lín_1='\t', lín_otras='\t\t'),
                 cortar_líns(dic_var['unidades'], símismo.lím_línea, lín_1='\t', lín_otras='\t\t'),
                 cortar_líns(dic_var['comentarios'], símismo.lím_línea, lín_1='\t~\t', lín_otras='\t\t'), '\t' + '|']

        return texto

    def obt_unidad_tiempo(símismo):
        pass

    def iniciar_modelo(símismo, nombre_corrida, tiempo_final):
        pass

    def cambiar_vals_modelo_interno(símismo, valores):
        pass

    def incrementar(símismo, paso):
        pass

    def leer_vals(símismo):
        pass

    def cerrar_modelo(símismo):
        pass


class ModeloVensim(EnvolturaMDS):
    """
    Esta es la envoltura para modelos de tipo VENSIM. Puede leer y controlar (casi) cualquier modelo VENSIM para que
    se pueda emplear en Tinamit.
    Necesitarás la versión DSS de VENSIM para que funcione en Tinamit.
    """

    ext_arch_egr = '.vdf'

    def __init__(símismo, archivo):
        """
        La función de inicialización del modelo. Creamos el vínculo con el DLL de VENSIM y cargamos el modelo
        especificado.

        :param archivo: El archivo del modelo que quieres cargar en formato .vpm.
        :type archivo: str
        """

        # Llamar el DLL de VENSIM.
        if dll_Vensim is None:
            raise OSError('Esta computadora no tiene el DLL de Vensim DSS.')
        else:
            símismo.dll = dll = ctypes.WinDLL(dll_Vensim)

        # Inicializar Vensim
        comanda_vensim(func=dll.vensim_command,
                       args=[''],
                       mensaje_error='Error iniciando VENSIM.')

        # Cargar el modelo
        comanda_vensim(func=dll.vensim_command,
                       args='SPECIAL>LOADMODEL|%s' % archivo,
                       mensaje_error='Eroor cargando el modelo de VENSIM.')

        # Parámetros estéticos de ejecución.
        comanda_vensim(func=dll.vensim_be_quiet, args=[2],
                       mensaje_error='Error en la comanda "vensim_be_quiet".',
                       val_error=-1)

        # El paso para incrementar
        símismo.paso = 1

        # Una lista de variables editables
        símismo.editables = []

        # Inicializar ModeloVENSIM como una EnvolturaMDS.
        super().__init__(archivo=archivo)

    def inic_vars(símismo):
        """
        Inicializamos el diccionario de variables del modelo VENSIM.
        """

        # Sacar las unidades y las dimensiones de los variables, e identificar los variables constantes
        for l in [símismo.editables, símismo.constantes, símismo.niveles, símismo.auxiliares, símismo.flujos,
                  símismo.variables, símismo.dic_info_vars]:
            l.clear()

        editables = símismo.editables
        constantes = símismo.constantes
        niveles = símismo.niveles
        auxiliares = símismo.auxiliares
        flujos = símismo.flujos
        dic_info_vars = símismo.dic_info_vars

        # Primero, verificamos el tamañano de memoria necesario para guardar una lista de los nombres de los variables.

        mem = ctypes.create_string_buffer(0)  # Crear una memoria intermedia

        # Verificar el tamaño necesario
        tamaño_nec = comanda_vensim(func=símismo.dll.vensim_get_varnames,
                                    args=['*', 0, mem, 0],
                                    mensaje_error='Error obteniendo eñ tamaño de los variables VENSIM.',
                                    val_error=-1, devolver=True
                                    )

        mem = ctypes.create_string_buffer(tamaño_nec)  # Una memoria intermedia con el tamaño apropiado

        # Guardar y decodar los nombres de los variables.
        comanda_vensim(func=símismo.dll.vensim_get_varnames,
                       args=['*', 0, mem, tamaño_nec],
                       mensaje_error='Error obteniendo los nombres de los variables de VENSIM.',
                       val_error=-1
                       )
        variables = [x for x in mem.raw.decode().split('\x00') if x]

        # Quitar los nombres de variables VENSIM genéricos de la lista.
        for i in ['FINAL TIME', 'TIME STEP', 'INITIAL TIME', 'SAVEPER', 'Time']:
            if i in variables:
                variables.remove(i)

        # Sacar los nombres de variables editables
        comanda_vensim(func=símismo.dll.vensim_get_varnames,
                       args=['*', 12, mem, tamaño_nec],
                       mensaje_error='Error obteniendo los nombres de los variables editables ("Gaming") de '
                                     'VENSIM.',
                       val_error=-1
                       )

        editables.extend([x for x in mem.raw.decode().split('\x00') if x])

        for var in variables:
            # Para cada variable...

            # Sacar sus unidades
            unidades = símismo.obt_atrib_var(var, cód_attrib=1)

            # Verificar el tipo del variable
            tipo_var = símismo.obt_atrib_var(var, cód_attrib=14)

            # No incluir a los variables de verificación (pruebas de modelo) Vensim
            if tipo_var == 'Constraint':
                variables.remove(var)
                continue

            # Guardamos los variables constantes en una lista.
            if tipo_var == 'Constant':
                constantes.append(var)
            elif tipo_var == 'Level':
                niveles.append(var)
            elif tipo_var == 'Auxiliary':
                auxiliares.append(var)

            # Sacar las dimensiones del variable
            subs = símismo.obt_atrib_var(var, cód_attrib=9)

            if len(subs):
                dims = (len(subs),)  # Para hacer: soporte para más que 1 dimensión
                nombres_subs = subs
            else:
                dims = (1,)
                nombres_subs = None

            # Leer la descripción del variable.
            info = símismo.obt_atrib_var(var, 2)

            # Actualizar el diccionario de variables.
            # Para cada variable, creamos un diccionario especial, con su valor y unidades. Puede ser un variable
            # de ingreso si es de tipo editable ("Gaming"), y puede ser un variable de egreso si no es un valor
            # constante.
            dic_var = {'val': None if dims == (1,) else np.empty(dims),
                       'unidades': unidades,
                       'ingreso': var in editables,
                       'dims': dims,
                       'subscriptos': nombres_subs,
                       'egreso': var not in constantes,
                       'info': info}

            # Guadar el diccionario del variable en el diccionario general de variables.
            símismo.variables[var] = dic_var

            # Guardar información adicional
            hijos = símismo.obt_atrib_var(var, 5)
            parientes = símismo.obt_atrib_var(var, 4)
            ec = símismo.obt_atrib_var(var, 3)
            dic_info_vars[var] = {
                'hijos': hijos,
                'parientes': parientes,
                'ec': ec}

        # Actualizar los auxiliares
        for var in símismo.auxiliares.copy():
            for hijo in dic_info_vars[var]['hijos']:
                if hijo in símismo.niveles:
                    flujos.append(var)
                    if var in auxiliares:
                        auxiliares.remove(var)

    def obt_unidad_tiempo(símismo):
        """
        Aquí, sacamos las unidades de tiempo del modelo VENSIM.

        :return: Las unidades de tiempo.
        :rtype: str

        """

        # Leer las unidades de tiempo
        unidades = símismo.obt_atrib_var(var='TIME STEP', cód_attrib=1,
                                         mns_error='Error obteniendo el paso de tiempo para el modelo Vensim.')

        return unidades

    def iniciar_modelo(símismo, tiempo_final, nombre_corrida):
        """
        Acciones necesarias para iniciar el modelo VENSIM.

        :param nombre_corrida: El nombre de la corrida del modelo.
        :type nombre_corrida: str

        :param tiempo_final: El tiempo final de la simulación.
        :type tiempo_final: int

        """

        # En Vensim, tenemos que incializar los valores de variables constantes antes de empezar la simulación.
        símismo.cambiar_vals({var: val for var, val in símismo.vals_inic.items()
                              if var in símismo.constantes})

        # Establecer el nombre de la corrida.
        comanda_vensim(func=símismo.dll.vensim_command,
                       args="SIMULATE>RUNNAME|%s" % nombre_corrida,
                       mensaje_error='Error iniciando la corrida VENSIM.')

        # Establecer el tiempo final.
        comanda_vensim(func=símismo.dll.vensim_command,
                       args='SIMULATE>SETVAL|%s = %i' % ('FINAL TIME', tiempo_final),
                       mensaje_error='Error estableciendo el tiempo final para VENSIM.')

        # Iniciar la simulación en modo juego ("Game"). Esto permitirá la actualización de los valores de los variables
        # a través de la simulación.
        comanda_vensim(func=símismo.dll.vensim_command,
                       args="MENU>GAME",
                       mensaje_error='Error inicializando el juego VENSIM.')

        # Aplicar los valores iniciales de variables editables (los cuales no se pueden cambiar después)
        símismo.cambiar_vals({var: val for var, val in símismo.vals_inic.items()
                              if var not in símismo.constantes})

    def cambiar_vals_modelo_interno(símismo, valores):
        """
        Esta función cambiar los valores de variables en VENSIM. Notar que únicamente los variables identificados como
        de tipo "Gaming" en el modelo podrán actualizarse.

        :param valores: Un diccionario de variables y sus nuevos valores.
        :type valores: dict

        """

        for var, val in valores.items():
            # Para cada variable para cambiar...

            if símismo.variables[var]['dims'] == (1,):
                # Si el variable no tiene dimensiones (subscriptos)...

                # Actualizar el valor en el modelo VENSIM.
                comanda_vensim(func=símismo.dll.vensim_command,
                               args='SIMULATE>SETVAL|%s = %f' % (var, val),
                               mensaje_error='Error cambiando el variable %s.' % var)
            else:
                # Para hacer: opciones de dimensiones múltiples
                # La lista de subscriptos
                subs = símismo.variables[var]['subscriptos']
                if isinstance(val, np.ndarray):
                    matr = val
                else:
                    matr = np.empty(len(subs))
                    matr[:] = val

                for n, s in enumerate(subs):
                    var_s = var + s
                    val_s = matr[n]

                    comanda_vensim(func=símismo.dll.vensim_command,
                                   args='SIMULATE>SETVAL|%s = %f' % (var_s, val_s),
                                   mensaje_error='Error cambiando el variable %s.' % var_s)

    def incrementar(símismo, paso):
        """
        Esta función avanza la simulación VENSIM de ``paso`` pasos.

        :param paso: El número de pasos para tomar.
        :type paso: int

        """

        # Establecer el paso.
        if paso != símismo.paso:
            comanda_vensim(func=símismo.dll.vensim_command,
                           args="GAME>GAMEINTERVAL|%i" % paso,
                           mensaje_error='Error estableciendo el paso de VENSIM.')
            símismo.paso = paso

        # Avanzar el modelo.
        comanda_vensim(func=símismo.dll.vensim_command,
                       args="GAME>GAMEON", mensaje_error='Error para incrementar VENSIM.')

    def leer_vals(símismo):
        """
        Este método lee los valores intermediaros de los variables del modelo VENSIM. Para ahorrar tiempo, únicamente
        lee esos variables que están en la lista de ``ModeloVENSIM.vars_saliendo``.
        """

        # Una memoria
        mem_inter = ctypes.create_string_buffer(4)

        for var in símismo.vars_saliendo:
            # Para cada variable que está conectado con el modelo biofísico...

            if símismo.variables[var]['dims'] == (1,):
                # Si el variable no tiene dimensiones (subscriptos)...

                # Leer su valor.
                comanda_vensim(func=símismo.dll.vensim_get_val,
                               args=[var, mem_inter],
                               mensaje_error='Error con VENSIM para leer variables.')

                # Decodar
                val = struct.unpack('f', mem_inter)[0]

                # Guardar en el diccionario interno.
                símismo.variables[var]['val'] = val

            else:
                for n, s in enumerate(símismo.variables[var]['subscriptos']):
                    var_s = var + s

                    # Leer su valor.
                    comanda_vensim(func=símismo.dll.vensim_get_val,
                                   args=[var_s, mem_inter],
                                   mensaje_error='Error con VENSIM para leer variables.')

                    # Decodar
                    val = struct.unpack('f', mem_inter)[0]

                    # Guardar en el diccionario interno.
                    símismo.variables[var]['val'][n] = val  # Para hacer: opciones de dimensiones múltiples

    def cerrar_modelo(símismo):
        """
        Cierre la simulación Vensim.
        """

        # Llamar la comanda para terminar la simulación.
        comanda_vensim(func=símismo.dll.vensim_command,
                       args="GAME>ENDGAME",
                       mensaje_error='Error para terminar la simulación VENSIM.')

    def verificar_vensim(símismo):
        """
        Esta función regresa el estatus de Vensim. Es particularmente útil para desboguear (no tiene uso en las
        otras funciones de esta clase, y se incluye como ayuda a la programadora.)

        :return: Código de estatus Vensim:
            | 0 = Vensim está listo
            | 1 = Vensim está en una simulación activa
            | 2 = Vensim está en una simulación, pero no está respondiendo
            | 3 = Malas noticias
            | 4 = Error de memoria
            | 5 = Vensim está en modo de juego
            | 6 = Memoria no libre. Llamar vensim_command() debería de arreglarlo.
            | 16 += ver documentación de Vensim para vensim_check_status() en la sección de DLL (Suplemento DSS)
        :rtype: int

        """

        # Obtener el estatus.
        estatus = comanda_vensim(func=símismo.dll.vensim_check_status,
                                 args=[],
                                 mensaje_error='Error verificando el estatus de VENSIM. De verdad, la cosa'
                                               'te va muy mal.',
                                 val_error=-1, devolver=True)
        return int(estatus)

    def obt_atrib_var(símismo, var, cód_attrib, mns_error=None):
        """

        :param var:
        :type var:
        :param cód_attrib:
        :type cód_attrib:
        :param tx_op:
        :type tx_op:
        :return:
        :rtype:
        """

        if cód_attrib in [4, 5, 6, 7, 8, 9, 10]:
            lista = True
        elif cód_attrib in [1, 2, 3, 11, 12, 13, 14]:
            lista = False
        else:
            raise ValueError('Código "{}" no reconocido para la comanda Vensim de obtener atributos de variables.'
                             .format(cód_attrib))

        if mns_error is None:
            l_atrs = ['las unidades', 'la descipción', 'la ecuación', 'las causas', 'las consecuencias',
                      'la causas iniciales', 'las causas activas', 'los subscriptos',
                      'las combinaciones de subscriptos', 'los subscriptos de gráfico', 'el mínimo', 'el máximo',
                      'el rango', 'el tipo']
            mns_error1 = 'Error leyendo el tamaño de memoria para {} del variable "{}" en Vensim' \
                .format(l_atrs[cód_attrib - 1], var)
            mns_error2 = 'Error leyendo {} del variable "{}" en Vensim.'.format(l_atrs[cód_attrib - 1], var)
        else:
            mns_error1 = mns_error2 = mns_error

        mem = ctypes.create_string_buffer(10)
        tmñ = comanda_vensim(func=símismo.dll.vensim_get_varattrib,
                             args=[var, cód_attrib, mem, 0],
                             mensaje_error=mns_error1,
                             val_error=-1,
                             devolver=True)

        mem = ctypes.create_string_buffer(tmñ)
        comanda_vensim(func=símismo.dll.vensim_get_varattrib,
                       args=[var, cód_attrib, mem, tmñ],
                       mensaje_error=mns_error2,
                       val_error=-1)

        if lista:
            return [x for x in mem.raw.decode().split('\x00') if x]
        else:
            return mem.value.decode()


def comanda_vensim(func, args, mensaje_error=None, val_error=None, devolver=False):
    """
    Esta función sirve para llamar todo tipo de comanda VENSIM.

    :param func: La función DLL a llamar.
    :type func: callable

    :param args: Los argumento a pasar a la función. Si no hay, usar una lista vacía.
    :type args: list | str

    :param mensaje_error: El mensaje de error para mostrar si hay un error en la comanda.
    :type mensaje_error: str

    :param val_error: Un valor de regreso VENSIM que indica un error para esta función. Si se deja ``None``, todos
      valores que no son 1 se considerarán como erróneas.
    :type val_error: int

    :param devolver: Si se debe devolver el valor devuelto por VENSIM o no.
    :type devolver: bool

    """

    # Asegurarse que args es una lista
    if type(args) is not list:
        args = [args]

    # Encodar en bytes todos los argumentos de texto.
    for n, a in enumerate(args):
        if type(a) is str:
            args[n] = a.encode()

    # Llamar la función VENSIM y guardar el resultado.
    resultado = func(*args)

    # Verificar su hubo un error.
    if val_error is None:
        error = (resultado != 1)
    else:
        error = (resultado == val_error)

    # Si hubo un error, avisar el usuario.
    if error:
        if mensaje_error is None:
            mensaje_error = 'Error con la comanda VENSIM.'

        mensaje_error += ' Código de error {}.'.format(resultado)

        raise OSError(mensaje_error)

    # Devolver el valor devuelto por la función VENSIM, si aplica.
    if devolver:
        return resultado
