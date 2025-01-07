 
from http.server import BaseHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET
import http.client
import json

class SOAPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Leer el contenido de la solicitud
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Procesar la solicitud SOAP entrante
        soap_action = self.headers.get('SOAPAction', '')
        if "ObtieneMarcasContratistas" in soap_action:
            response_data = self.handle_obtiene_marcas_contratistas(post_data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_error(400, "Invalid SOAPAction")

    def handle_obtiene_marcas_contratistas(self, request_data):
        # Extraer los datos de la solicitud SOAP
        tree = ET.fromstring(request_data.decode('utf-8'))
        namespace = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
        body = tree.find('soap:Body', namespace)
        token = body.find('.//token').text
        desde = body.find('.//Desde').text
        hasta = body.find('.//Hasta').text

        # Enviar la solicitud al servidor externo y obtener la respuesta
        external_response = self.send_soap_to_external_server(token, desde, hasta)

        # Convertir la respuesta SOAP a JSON
        response_json = self.parse_soap_response_to_json(external_response)
        return response_json

    def send_soap_to_external_server(self, token, desde, hasta):
        # Crear el cuerpo SOAP para el servidor externo
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

        # Conexión al servidor externo
        conn = http.client.HTTPConnection("biocov.smartime.cl")
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://tempuri.org/ObtieneMarcasContratistas"
        }
        conn.request("POST", "/Reports/WSMolymet.asmx", soap_body, headers)
        response = conn.getresponse()
        response_data = response.read().decode('utf-8')
        conn.close()

        # Retornar la respuesta SOAP
        return response_data

    def parse_soap_response_to_json(self, soap_response):
        # Parsear la respuesta SOAP
        tree = ET.fromstring(soap_response)
        namespace = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/'}
        body = tree.find('soap:Body', namespace)

        # Extraer datos del nodo de respuesta
        response_node = body.find('.//ObtieneMarcasContratistasResponse', namespace)
        if response_node is None:
            return {"error": "No data found"}

        # Convertir los datos relevantes a JSON
        result_data = {}
        for child in response_node:
            result_data[child.tag] = child.text

        return result_data

# Configurar y ejecutar el servidor HTTP
def run_server():
    server_address = ('', 8000)  # Escucha en el puerto 8000
    httpd = HTTPServer(server_address, SOAPHandler)
    print("Servidor ejecutándose en el puerto 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()


