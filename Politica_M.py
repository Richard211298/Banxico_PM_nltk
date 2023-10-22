import requests
from bs4 import BeautifulSoup
import pandas as pd
import re #para verificar fechas
import difflib #para unir agrupar texto
from nltk.tokenize import word_tokenize
from nltk import pos_tag
import nltk

# descargar si no los tengo
nltk.download('averaged_perceptron_tagger')



class Politicas_BANXICO:
    def __init__(self):
        pass

    def Table_only_Year(self):

        def modificar_year(year):
            if len(year) == 2:
                return "20" + year
            else:
                return year
            
        try:
            web = 'https://www.banxico.org.mx/publicaciones-y-prensa/anuncios-de-las-decisiones-de-politica-monetaria/anuncios-politica-monetaria-t.html'
            content = requests.get(web).text
            soup = BeautifulSoup(content, 'lxml')
            tabla_td = soup.find_all('td')
            fecha = []
            for td in tabla_td:
                if re.match(r'\d{2}/\d{2}/\d{2}', td.text):
                    fecha.append(td.text)

            df_only_years = pd.DataFrame(fecha)
            df_only_years[0] = df_only_years[0].str.replace("\n", "")
            df_only_years[['Day', 'Month', 'Year']] = df_only_years[0].str.split('/', expand=True)
            df_only_years["Year"] = df_only_years["Year"].apply(modificar_year)
            # Elimina los años duplicados
            años_únicos = sorted(list(set(df_only_years["Year"])),reverse=True)
            return años_únicos
        except Exception as e:
            return {"Error al traer solo los años": str(e)}
        

    def Politica_monetaria(self):
        # URL de la página web
        web = 'https://www.banxico.org.mx/publicaciones-y-prensa/anuncios-de-las-decisiones-de-politica-monetaria/anuncios-politica-monetaria-t.html'
        try:
            # Realiza la solicitud HTTP
            response = requests.get(web)
            # Verifica si la solicitud fue exitosa
            if response.status_code == 200:
                content = response.text
                # Analiza el contenido HTML con BeautifulSoup
                soup = BeautifulSoup(content, 'lxml')
                # Encuentra todas las etiquetas <td>
                tabla_td = soup.find_all('td')
                fecha=[]
                noticia=[]
                for td in tabla_td:
                    if re.match(r'\d{2}/\d{2}/\d{2}', td.text):  
                        # Comprueba si el contenido coincide con el formato de fecha
                        fecha.append(td.text)
                    else:
                        noticia.append(td.text)
                tabla_general = [fecha, noticia]
                df_tabla_general=pd.DataFrame(tabla_general)
                # transponer
                df_tabla_general=df_tabla_general.T

                # dict_tabla_general = df_tabla_general.to_dict(orient='list')
                return df_tabla_general
            else:
                return {"Error al solicitar la página: Código de estado": str(response.status_code)}
        except Exception as e:
            return {"Error al obtener datos": str(e)}

    ########################

    # funcion para separar por año la tabla


    def Table_Year(self,tabla,years):
            
            def modificar_year(year):
                if len(year) == 2:
                    return "20" + year
                else:
                    return year
            
            try:
                tabla_sucia=pd.DataFrame(tabla)
                tabla_sucia[0] = tabla_sucia[0].str.replace("\n", "")
                tabla_sucia[1]=tabla_sucia[1].str.replace("\n\nTexto completo\n",'')
                tabla_sucia[['Day','Month','Year']] = tabla_sucia[0].str.split('/', expand=True)
                tabla_sucia["Year"] = tabla_sucia["Year"].apply(modificar_year)
                tabla_sucia.drop(0, axis=1, inplace=True)
                tabla_year=tabla_sucia[tabla_sucia["Year"]==years]
                tabla_year = tabla_year.drop("Day", axis=1)
                tabla_year = tabla_year.drop("Month", axis=1)

                return tabla_year

            except Exception as e:
                return {"Error al limpiar datos por año": str(e)}

    def resumen_politica_monetaria(self,tabla):
        try:
            num_filas=len(tabla[1])

            tabla_tag=[] #lista para añmacenar texto de año y pasar a tag
            palabras_esenciales = [] #lista para almacenar palabras importantes para clasificar
            texto_esencial=[] # lista sin elementos tipo el,para ,etc
            textos_agrupados = {} #lugar donde se almacena la clasificacion de oraciones similares
            conteo_elementos_por_grupo = []  # Aquí almacenaremos el recuento de elementos por grupo
            nombre_elemento_por_grupo=[] # aqui almacenaremos el nombre de cada grupo
            palabras_no_text=[] #oraciones que tokenize no procesa para analizar despues
            tabla_resumen_politica_monetaria=[]

            for i in range(num_filas):
                texto = tabla.iloc[i, 0]
                if isinstance(texto, str):
                # La variable 'texto' es una cadena (string)
                    tabla_tag.append(pos_tag(word_tokenize(texto)))
                else:
                    palabras_no_text.append(texto)

            for pos_tags in tabla_tag:
                # Filtra las palabras con etiquetas POS de sustantivos (NN y NNS) y verbos (VB y VBD)
                palabras_filtradas = [palabra for palabra, etiqueta in pos_tags if etiqueta in ['NN', 'NNS', 'VB', 'VBD','CD','JJ','NNP']]
                palabras_esenciales.append(palabras_filtradas)

            for oracion in palabras_esenciales:
                # if not para negar letras
                texto_filtrado=[letras for letras in oracion if not letras in ['El','la','para']]
                texto_esencial.append(texto_filtrado)

            texto_unido = [' '.join(oracion) for oracion in texto_esencial]

            # agrupacion por textos similares
            def similar(a, b):
                return difflib.SequenceMatcher(None, a, b).ratio()

            # Agrupar textos similares

            tabla_sucia=pd.DataFrame(texto_unido)
            # print(tabla_sucia)

            for i, texto1 in enumerate(tabla_sucia[0]):
                grupo = [texto1]
                for j, texto2 in enumerate(tabla_sucia[0]):
                    if i != j and similar(texto1, texto2) > 0.99:  # Ajusta el umbral según tus necesidades
                        grupo.append(texto2)
                textos_agrupados[i] = grupo

            # Eliminar grupos duplicados
            grupos_unicos = list(set(tuple(grupo) for grupo in textos_agrupados.values()))

            for grupo in grupos_unicos:
                cantidad_elementos = len(grupo)
                nombre_elemento_por_grupo.append(grupo[0])
                conteo_elementos_por_grupo.append(cantidad_elementos)

            num_filas_aplicacion_de_politica=len(conteo_elementos_por_grupo)

            for i in range(num_filas_aplicacion_de_politica):
                tabla_resumen_politica_monetaria.append([nombre_elemento_por_grupo[i],conteo_elementos_por_grupo[i]])

            return tabla_resumen_politica_monetaria

        except Exception as e:
            return {"Error al hacer resumen de la politica monetaria": str(e)}


