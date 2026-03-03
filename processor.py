import re
import json
import cv2
import pytesseract

class OCR_Billetes(OCR):
    def __init__(self, blacklist_path="blacklist.json"):
        super().__init__()
        self.blacklist = self.load_blacklist(blacklist_path)
        # Expresión regular para series: Busca una letra seguida de 7-9 dígitos o viceversa
        self.serie_pattern = re.compile(r'([A-Z])(\d{7,9})|(\d{7,9})([A-Z])')

    def load_blacklist(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            return {"ranges": {}}

    def validar_serie(self, texto_detectado, denominacion_seleccionada):
        """
        Lógica de robustez: Analiza si el texto es una serie y si es legal.
        """
        match = self.serie_pattern.search(texto_detectado.upper().replace(" ", ""))
        if not match:
            return None # No se detectó una serie válida aún

        # Extraer letra y número
        grupos = match.groups()
        letra = grupos[0] if grupos[0] else grupos[3]
        numero_str = grupos[1] if grupos[1] else grupos[2]
        numero = int(numero_str)

        # REGLA 1: Serie A es siempre legal
        if letra == 'A':
            return True, f"Serie A-{numero}: LEGAL"

        # REGLA 2: Serie B - Validar contra lista negra
        if letra == 'B':
            rangos = self.blacklist.get("ranges", {}).get(str(denominacion_seleccionada), [])
            for r in rangos:
                if r["del"] <= numero <= r["al"]:
                    return False, f"Serie B-{numero}: ILEGAL (Lista Negra)"
            
            return True, f"Serie B-{numero}: LEGAL"
        
        return True, "Serie Desconocida: Revisión Manual"

    def ocr_avanzado(self, denominacion):
        """
        Procesamiento con detección de columnas y filtrado de ruido.
        """
        while not self.stopped:
            if self.exchange is not None:
                frame = self.exchange.frame
                
                # Pre-procesamiento para robustez (Tfaking/Limpieza)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Aumentamos contraste para números pequeños
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                # Obtener datos detallados (columnas, filas, confianza)
                data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
                
                resultado_final = None
                
                for i in range(len(data['text'])):
                    conf = int(data['conf'][i])
                    texto = data['text'][i].strip()
                    
                    if conf > 60 and len(texto) > 5: # Filtro de confianza y longitud
                        res = self.validar_serie(texto, denominacion)
                        if res:
                            resultado_final = res
                            break # Encontramos la serie, dejamos de buscar en este frame
                
                self.current_status = resultado_final # (Boolean, Mensaje)

def dibujar_interfaz_pro(frame, status_info):
    """
    Dibuja la pantalla en rojo o verde según la legalidad.
    """
    overlay = frame.copy()
    h, w, _ = frame.shape

    if status_info:
        is_legal, mensaje = status_info
        color = (0, 255, 0) if is_legal else (0, 0, 255) # Verde o Rojo
        
        # Efecto de pantalla completa (márgenes brillantes)
        cv2.rectangle(overlay, (0,0), (w, h), color, -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Cuadro de texto profesional
        cv2.putText(frame, mensaje, (50, h // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    
    return frame
