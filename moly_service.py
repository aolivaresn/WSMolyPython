from http.server import BaseHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET

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
            self.send_header('Content-Type', 'text/xml; charset=utf-8')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
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

        # Generar la respuesta SOAP
        response_data = self.generate_soap_response(token, desde, hasta)
        return response_data

    def generate_soap_response(self, token, desde, hasta):
        # Construir una respuesta SOAP de ejemplo
        response_body = f"""
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <ObtieneMarcasContratistasResponse xmlns="http://tempuri.org/">
                    <Marcas>
                        <Marca>
                            <Token>{token}</Token>
                            <Desde>{desde}</Desde>
                            <Hasta>{hasta}</Hasta>
                            <Resultado>Ejemplo de marca registrada</Resultado>
                        </Marca>
                    </Marcas>
                </ObtieneMarcasContratistasResponse>
            </soap:Body>
        </soap:Envelope>
        """
        return response_body

# Configurar y ejecutar el servidor HTTP
def run_server():
    server_address = ('', 8000)  # Escucha en el puerto 8000
    httpd = HTTPServer(server_address, SOAPHandler)
    print("Servidor SOAP ejecutándose en el puerto 8000...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()

