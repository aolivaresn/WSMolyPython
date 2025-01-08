from http.server import BaseHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET
import http.client
import json
import re
from datetime import datetime

# Configuración global
SOAP_SERVER = "biocov.smartime.cl"
SOAP_PATH = "/Reports/WSMolymet.asmx"
PORT = 8000
TOKEN = "$Uyhha!rEpL"

# Validar formato de fechas
def validate_datetime_format(date_text):
    try:
        datetime.strptime(date_text, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

# Validar formato de token (opcional: puedes ajustar esta función si hay un formato específico)
def validate_token_format(token):
    # Ejemplo: token debe ser alfanumérico y de longitud exacta de 12 caracteres
    return re.match(r'^[a-zA-Z0-9!@#$%^&*()_+=-]{12}$', token) is not None

# Función para enviar solicitudes SOAP al servidor externo
def send_soap_request(desde, hasta, token):
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <ObtieneMarcasContratistas xmlns="http://tempuri.org/">
                <token>{token}</token>
                <Desde>{desde}</Desde>
                <Hasta>{hasta}</Hasta>
            </ObtieneMarcasContratistas>
        </soap:Body>
    </soap:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/ObtieneMarcasContratistas"
    }

    try:
        conn = http.client.HTTPSConnection(SOAP_SERVER)
        conn.request("POST", SOAP_PATH, soap_body, headers)
        response = conn.getresponse()

        if response.status != 200:
            raise ConnectionError(f"Error del servidor: {response.status} {response.reason}")

        response_data = response.read().decode("utf-8")
        conn.close()
        return response_data

    except Exception as e:
        raise ConnectionError(f"Fallo en la conexión al servidor SOAP: {str(e)}")

# Función para convertir la respuesta SOAP a JSON
def parse_soap_to_json(soap_response):
    try:
        tree = ET.fromstring(soap_response)
        namespace = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
        body = tree.find('soap:Body', namespace)

        response_node = body.find('.//ObtieneMarcasContratistasResponse', namespace)
        if response_node is None:
            raise ValueError("No se encontraron datos en la respuesta SOAP")

        result_data = {}
        for child in response_node:
            result_data[child.tag] = child.text

        return result_data

    except Exception as e:
        return {"error": f"Fallo al parsear la respuesta SOAP: {str(e)}"}

# Clase para manejar las solicitudes HTTP
class SOAPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            desde, hasta, token = self.extract_parameters(post_data)

            # Validar parámetros
            if not desde or not hasta or not token:
                raise ValueError("Parámetros 'Desde', 'Hasta' y 'token' son requeridos")
            if not validate_datetime_format(desde) or not validate_datetime_format(hasta):
                raise ValueError("Los parámetros 'Desde' y 'Hasta' deben estar en formato 'YYYY-MM-DD HH:MM'")
            if not validate_token_format(token):
                raise ValueError("El formato del token es inválido")
            if token != TOKEN:
                raise PermissionError("Token inválido o no autorizado")

            soap_response = send_soap_request(desde, hasta, token)
            json_response = parse_soap_to_json(soap_response)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(json_response).encode("utf-8"))

        except PermissionError as pe:
            self.send_error(403, f"Acceso denegado: {str(pe)}")
        except Exception as e:
            self.send_error(500, f"Error interno: {str(e)}")

    def extract_parameters(self, post_data):
        try:
            tree = ET.fromstring(post_data.decode("utf-8"))
            namespace = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
            body = tree.find('soap:Body', namespace)

            token = body.find('.//token').text
            desde = body.find('.//Desde').text
            hasta = body.find('.//Hasta').text
            return desde, hasta, token

        except Exception as e:
            raise ValueError(f"Error al extraer parámetros: {str(e)}")

# Función para ejecutar el servidor HTTP
def run_server():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SOAPHandler)
    print(f"Servidor ejecutándose en el puerto {PORT}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
