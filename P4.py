import flet as ft
import threading
import time
import datetime
import json
import os
import pyodbc
from uma import ContenedorUMA
from manometro import ContenedorManometro
from configuracion import ContenedorConfiguracion
from alertas import SistemaAlertas, AlertasView

# ========== CLASE PARA CONEXIÓN A BASE DE DATOS ==========
class DatabaseConnection:
    def __init__(self):
        self.server_ip = "192.168.1.XX"  # Cambiado a tu servidor
        self.database = "Prueba"
        self.username = "sa"
        self.password = "Contrasena123"
        self.connection = None
        self.cursor = None
        self.is_connected = False
        
    def connect(self):
        """Intenta establecer conexión con SQL Server"""
        try:
            connection_string = (
                'DRIVER={SQL Server};'
                f'SERVER={self.server_ip};'
                f'DATABASE={self.database};'
                f'UID={self.username};'
                f'PWD={self.password}'
            )
            
            print(f"🔗 Intentando conectar a {self.server_ip}...")
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            self.is_connected = True
            
            # Verificar conexión
            self.cursor.execute("SELECT 1")
            
            return True, "✅ Conexión exitosa a SQL Server"
            
        except pyodbc.OperationalError as e:
            return False, f"❌ Error de conexión: No se puede conectar al servidor"
        except pyodbc.Error as e:
            return False, f"❌ Error de base de datos: {str(e)[:100]}"
        except Exception as e:
            return False, f"❌ Error inesperado: {str(e)[:100]}"
    
    def get_pressure_data(self, fila_index=0):
        """Obtiene los datos de presión de una fila específica de TM_SOL_09"""
        try:
            # Obtener todas las filas con un ID para poder navegar
            self.cursor.execute("""
                SELECT 
                    id,
                    presion_24, presion_30, presion_35, presion_36,
                    presion_50, presion_51, presion_52, presion_53,
                    presion_54, presion_55, presion_56, presion_57,
                    presion_58, presion_59, presion_60, presion_61,
                    presion_62, presion_63, presion_64, presion_65,
                    presion_66, presion_67, presion_68, presion_69,
                    presion_70, presion_72
                FROM TM_SOL_09 
                ORDER BY id
            """)
            
            rows = self.cursor.fetchall()
            
            if rows:
                # Si hay filas, obtener la fila específica (ciclada)
                if fila_index >= len(rows):
                    fila_index = 0  # Volver al inicio
                
                row = rows[fila_index]
                
                # Crear diccionario con los nombres de columna
                pressures = {}
                column_names = ['presion_24', 'presion_30', 'presion_35', 'presion_36',
                              'presion_50', 'presion_51', 'presion_52', 'presion_53',
                              'presion_54', 'presion_55', 'presion_56', 'presion_57',
                              'presion_58', 'presion_59', 'presion_60', 'presion_61',
                              'presion_62', 'presion_63', 'presion_64', 'presion_65',
                              'presion_66', 'presion_67', 'presion_68', 'presion_69',
                              'presion_70', 'presion_72']
                
                # Comenzar desde el índice 1 porque el índice 0 es el ID
                for i, col_name in enumerate(column_names):
                    key_name = col_name.replace('_', '-')
                    pressures[key_name] = float(row[i+1]) if row[i+1] is not None else 0
                
                return pressures, f"Fila {fila_index + 1} de {len(rows)}", len(rows)
            else:
                # Si no hay datos, retornar valores por defecto
                default_pressures = {f'presion-{i}': 0 for i in [24, 30, 35, 36, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 72]}
                return default_pressures, "Sin datos", 0
                
        except Exception as e:
            print(f"❌ Error obteniendo datos de presión: {e}")
            default_pressures = {f'presion-{i}': 0 for i in [24, 30, 35, 36, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 72]}
            return default_pressures, None, 0
    
    def get_uma_data(self, fila_index=0):
        """Obtiene los datos de UMA 09 de una fila específica de UMA_09"""
        try:
            self.cursor.execute("""
                SELECT 
                    id,
                    temperatura,
                    humedad,
                    fel_1,
                    fel_2,
                    fel_3,
                    fel_ng
                FROM UMA_09 
                ORDER BY id
            """)
            
            rows = self.cursor.fetchall()
            
            if rows:
                # Si hay filas, obtener la fila específica (ciclada)
                if fila_index >= len(rows):
                    fila_index = 0  # Volver al inicio
                
                row = rows[fila_index]
                
                uma_data = {
                    'temperatura-09': float(row.temperatura) if row.temperatura is not None else 0,
                    'humedad-09': float(row.humedad) if row.humedad is not None else 0,
                    'presion-fel_1-09': float(row.fel_1) if row.fel_1 is not None else 0,
                    'presion-fel_2-09': float(row.fel_2) if row.fel_2 is not None else 0,
                    'presion-fel_3-09': float(row.fel_3) if row.fel_3 is not None else 0,
                    'presion-ng-09': float(row.fel_ng) if row.fel_ng is not None else 0
                }
                return uma_data, f"Fila {fila_index + 1} de {len(rows)}", len(rows)
            else:
                # Si no hay datos, retornar valores por defecto
                default_uma = {
                    'temperatura-09': 0,
                    'humedad-09': 0,
                    'presion-fel_1-09': 0,
                    'presion-fel_2-09': 0,
                    'presion-fel_3-09': 0,
                    'presion-ng-09': 0
                }
                return default_uma, "Sin datos", 0
                
        except Exception as e:
            print(f"❌ Error obteniendo datos de UMA: {e}")
            default_uma = {
                'temperatura-09': 0,
                'humedad-09': 0,
                'presion-fel_1-09': 0,
                'presion-fel_2-09': 0,
                'presion-fel_3-09': 0,
                'presion-ng-09': 0
            }
            return default_uma, None, 0
    
    def insert_pressure_data(self, data_dict):
        """Actualiza los datos de presión en la tabla TM_SOL_09"""
        try:
            # Actualizar la fila existente en TM_SOL_09
            query = """
                UPDATE TOP (1) TM_SOL_09 
                SET 
                    presion_24 = ?, presion_30 = ?, presion_35 = ?, presion_36 = ?,
                    presion_50 = ?, presion_51 = ?, presion_52 = ?, presion_53 = ?,
                    presion_54 = ?, presion_55 = ?, presion_56 = ?, presion_57 = ?,
                    presion_58 = ?, presion_59 = ?, presion_60 = ?, presion_61 = ?,
                    presion_62 = ?, presion_63 = ?, presion_64 = ?, presion_65 = ?,
                    presion_66 = ?, presion_67 = ?, presion_68 = ?, presion_69 = ?,
                    presion_70 = ?, presion_72 = ?
                WHERE id = (SELECT MIN(id) FROM TM_SOL_09)
            """
            
            # Extraer valores del diccionario
            values = (
                data_dict.get('presion-24', 0),
                data_dict.get('presion-30', 0),
                data_dict.get('presion-35', 0),
                data_dict.get('presion-36', 0),
                data_dict.get('presion-50', 0),
                data_dict.get('presion-51', 0),
                data_dict.get('presion-52', 0),
                data_dict.get('presion-53', 0),
                data_dict.get('presion-54', 0),
                data_dict.get('presion-55', 0),
                data_dict.get('presion-56', 0),
                data_dict.get('presion-57', 0),
                data_dict.get('presion-58', 0),
                data_dict.get('presion-59', 0),
                data_dict.get('presion-60', 0),
                data_dict.get('presion-61', 0),
                data_dict.get('presion-62', 0),
                data_dict.get('presion-63', 0),
                data_dict.get('presion-64', 0),
                data_dict.get('presion-65', 0),
                data_dict.get('presion-66', 0),
                data_dict.get('presion-67', 0),
                data_dict.get('presion-68', 0),
                data_dict.get('presion-69', 0),
                data_dict.get('presion-70', 0),
                data_dict.get('presion-72', 0)
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            print(f"✅ Datos de presión actualizados en TM_SOL_09")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando datos de presión: {e}")
            return False
    
    def insert_uma_data(self, data_dict):
        """Actualiza los datos de UMA en la tabla UMA_09"""
        try:
            # Actualizar la fila existente en UMA_09
            query = """
                UPDATE TOP (1) UMA_09 
                SET 
                    temperatura = ?,
                    humedad = ?,
                    fel_1 = ?,
                    fel_2 = ?,
                    fel_3 = ?,
                    fel_ng = ?
                WHERE id = (SELECT MIN(id) FROM UMA_09)
            """
            
            # Extraer valores del diccionario
            values = (
                data_dict.get('temperatura-09', 0),
                data_dict.get('humedad-09', 0),
                data_dict.get('presion-fel_1-09', 0),
                data_dict.get('presion-fel_2-09', 0),
                data_dict.get('presion-fel_3-09', 0),
                data_dict.get('presion-ng-09', 0)
            )
            
            self.cursor.execute(query, values)
            self.connection.commit()
            print(f"✅ Datos de UMA actualizados en UMA_09")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando datos de UMA: {e}")
            return False
    
    def get_all_data(self, fila_index=0):
        """Obtiene todos los datos de una fila específica (presión y UMA)"""
        try:
            # Obtener datos de presión
            pressures, pres_fecha, total_filas_pres = self.get_pressure_data(fila_index)
            
            # Obtener datos de UMA
            uma_data, uma_fecha, total_filas_uma = self.get_uma_data(fila_index)
            
            # Combinar ambos diccionarios
            all_data = {**pressures, **uma_data}
            
            # Usar el menor total de filas disponible
            total_filas = min(total_filas_pres, total_filas_uma)
            
            mensaje = f"Fila {fila_index + 1} de {total_filas}"
            
            return all_data, mensaje, total_filas
            
        except Exception as e:
            print(f"❌ Error obteniendo todos los datos: {e}")
            return None, None, 0
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.is_connected = False
            print("🔌 Conexión cerrada")
        except Exception as e:
            print(f"⚠️ Error cerrando conexión: {e}")

# ========== CLASE PARA RELOJ ==========
class Reloj:
    def __init__(self):
        self.horas_registradas = []
        self.archivo_horas = "horas.json"
        self.historial_registros = []
        self.archivo_historial = "historial_registros.json"
        self.reloj_activo = True
        self.ultima_ejecucion = {}
        self.callbacks = []
        self.historial_callbacks = []

        # Cargar horas guardadas
        self.cargar_horas()
        self.cargar_historial()
        self.iniciar()

    def agregar_callback(self, callback):
        """ Agrega una función que se ejecutará cuando suene una alarma """
        self.callbacks.append(callback)

    
    def agregar_callback_historial(self, callback):
        """Agrega una función que se ejecutará cuando se agregue un nuevo registro al historial"""
        self.historial_callbacks.append(callback)

    def cargar_horas(self):
        """ Carga las horas desde archivo horas.json """

        if os.path.exists(self.archivo_horas):
            try:
                with open(self.archivo_horas, "r") as file:
                    datos = json.load(file)
                    self.horas_registradas = [
                        datetime.datetime.strptime(h, "%H:%M").time()
                        for h in datos
                    ]
                print(f"\nHoras cargadas: {[h.strftime('%I:%M %p') for h in self.horas_registradas]}")
            except Exception as e:
                print(f"Error cargando horas: {e}")
                self.horas_registradas = []

    
    def cargar_historial(self):
        """Carga el historial desde archivo JSON"""
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, "r") as file:
                    self.historial_registros = json.load(file)
                print(f"RelojGlobal: Historial cargado ({len(self.historial_registros)} registros)")
            except Exception as e:
                print(f"RelojGlobal: Error cargando historial: {e}")
                self.historial_registros = []
        else:
            self.guardar_historial()

    def guardar_historial(self):
        """Guarda el historial en archivo JSON"""
        try:
            with open(self.archivo_historial, "w") as file:
                json.dump(self.historial_registros, file, indent=2)
        except Exception as e:
            print(f"RelojGlobal: Error guardando historial: {e}")

    def iniciar(self):
        """ Inicia el reloj en un hilo separado """
        if not hasattr(self, 'thread') or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.reloj_loop, daemon=True)
            self.thread.start()
            print("Reloj iniciado")

    def reloj_loop(self):
        """ Loop principal del reloj """
        while self.reloj_activo:
            try:
                self.ahora = datetime.datetime.now()

                # Revisar todas las horas guardadas
                for hora_obj in self.horas_registradas:
                    hora_actual_minuto = self.ahora.strftime("%I:%M %p")
                    segundos = self.ahora.strftime("%S")
                    hora_objetivo_str = hora_obj.strftime("%I:%M %p")

                    # Se ejecuta solo en el segundo 00
                    if hora_actual_minuto == hora_objetivo_str and segundos == "00":
                        h_obj = datetime.datetime.combine(self.ahora.date(), hora_obj)
                        clave = h_obj.strftime("%Y-%m-%d %H:%M")

                        if clave not in self.ultima_ejecucion:
                            self.ultima_ejecucion[clave] = True
                            self.ejecutar_alarma(hora_objetivo_str)

                time.sleep(1)

            except Exception as e:
                print(f"Error en el loop del reloj: {e}")
                time.sleep(1)

    def ejecutar_alarma(self, hora):
        """ Ejecuta todos los callbacks registrados """
        for callback in self.callbacks:
            try:
                callback(hora)
            except Exception as e:
                print(f"Error en callback: {e}")

    def agregar_hora(self, hora_time):
        """ Agrega una hora a la lista """
        if hora_time not in self.horas_registradas:
            self.horas_registradas.append(hora_time)
            self.guardar_horas()
            print(f"Hora de registro agregada: {hora_time.strftime('%I:%M %p')}")
            return True
        return False
    

    def eliminar_hora(self, hora_time):
        """Elimina una hora de la lista global"""
        if hora_time in self.horas_registradas:
            self.horas_registradas.remove(hora_time)
            self.guardar_horas()
            print(f"Hora de registro eliminada: {hora_time.strftime('%I:%M %p')}")
            return True
        return False
    

    def guardar_horas(self):
        """ Guarda las horas en archivo JSON """
        try:
            datos = [h.strftime("%H:%M") for h in self.horas_registradas]
            with open(self.archivo_horas, "w") as file:
                json.dump(datos, file)
        except Exception as e:
            print(f"Error guardando horas: {e}")

    def detener(self):
        """ Detiene el reloj """
        self.reloj_activo = False

    
    def agregar_al_historial(self, datos, tipo="Automatico", fuente="Reloj Global"):
        """Agrega un registro al historial"""
        registro = {
            "fecha": datetime.datetime.now().strftime("%d/%m/%y"),
            "hora": datetime.datetime.now().strftime('%I:%M %p'),
            "datos": datos,
            "tipo": tipo,
            "fuente": fuente
        }
        self.historial_registros.append(registro)
        self.guardar_historial()
        
        # Notificar a todos los callbacks
        for callback in self.historial_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"RelojGlobal: Error en callback de historial: {e}")
        
        return registro
    

    def obtener_registros_por_manometro(self, manometro_numero, limite=31):
        """
        Obtiene todos los registros históricos para un manómetro específico.
        manometro_numero: 1, 2 o 3
        limite: cantidad máxima de registros a retornar
        """
        registros_manometro = []
        
        # Filtrar registros para este manómetro (más recientes primero)
        for registro in self.historial_registros[::-1]:  # Invertir para obtener más recientes primero
            if 'datos' in registro:
                datos = registro['datos']
                # Extraer la presión del manómetro específico
                clave_presion = f'presion-{manometro_numero}'
                if clave_presion in datos:
                    # Convertir fecha y hora a datetime para ordenar
                    fecha_hora_str = f"{registro['fecha']} {registro['hora']}"
                    fecha_hora = datetime.datetime.strptime(fecha_hora_str, "%d/%m/%y %I:%M %p")
                    
                    registro_manometro = {
                        'fecha': registro['fecha'],
                        'hora': registro['hora'],
                        'fecha_hora': fecha_hora,
                        'presion': datos[clave_presion],
                        'tipo': registro.get('tipo', 'desconocido'),
                        'fuente': registro.get('fuente', 'desconocido')
                    }
                    registros_manometro.append(registro_manometro)
            
            # Limitar cantidad de registros
            if len(registros_manometro) >= limite:
                break
        
        # Ordenar por fecha_hora (más antiguo primero para gráfica de izquierda a derecha)
        registros_manometro.sort(key=lambda x: x['fecha_hora'])
        
        return registros_manometro
    

    def limpiar_historial(self):
        """Limpia todo el historial"""
        self.historial_registros = []
        self.guardar_historial()
        print("RelojGlobal: Historial limpiado")
        
        # Notificar a los callbacks
        for callback in self.historial_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"RelojGlobal: Error en callback de limpieza: {e}")

# ========== CLASE PARA INICIO DE SESION ==========
class LoginScreen:
    def __init__(self, page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success
        self.usuarios_file = "usuarios.json"
        
        # Crear instancia de base de datos
        self.db = DatabaseConnection()
        
        # Estado de conexión
        self.connecting = True
        self.connection_status = "Conectando a la base de datos..."
        self.connection_color = ft.Colors.BLUE
        
        # Spinner de conexión
        self.connection_spinner = ft.ProgressRing(
            width=20, 
            height=20, 
            stroke_width=2,
            color=ft.Colors.BLUE
        )
        
        # Texto de estado de conexión
        self.connection_status_text = ft.Text(
            self.connection_status,
            size=12,
            color=self.connection_color,
        )
        
        # Contenedor de estado de conexión
        self.connection_container = ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_50,
            content=ft.Row(
                spacing=10,
                controls=[
                    self.connection_spinner,
                    self.connection_status_text,
                ]
            )
        )
        
        # Cargar usuarios existentes
        self.cargar_usuarios()
        
        # Crear controles
        self.username_field = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.BLUE_900,
        )
        
        self.password_field = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK,
            width=300,
            password=True,
            can_reveal_password=True,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.BLUE_900,
        )
        
        self.login_button = ft.ElevatedButton(
            text="Iniciar Sesión",
            icon=ft.Icons.LOGIN,
            width=300,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_GREY_600,
                color=ft.Colors.WHITE,
            ),
            on_click=self.verificar_login,
            disabled=True,  # Deshabilitado hasta que termine la conexión
        )
        
        self.error_text = ft.Text(
            color=ft.Colors.RED,
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Detalles de conexión
        self.connection_details = ft.Container(
            padding=10,
            bgcolor=ft.Colors.BLUE_GREY_50,
            border_radius=10,
            visible=False,  # Oculto inicialmente
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.COMPUTER, size=14, color=ft.Colors.GREY_600),
                            ft.Text(f"Servidor: {self.db.server_ip}", size=12, color=ft.Colors.GREY_600),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.STORAGE, size=14, color=ft.Colors.GREY_600),
                            ft.Text(f"Base de datos: {self.db.database}", size=12, color=ft.Colors.GREY_600),
                        ]
                    ),
                ]
            )
        )
        
        # Botón para modo offline
        self.offline_button = ft.TextButton(
            text="Continuar en modo offline",
            on_click=self.use_offline_mode,
            visible=False,  # Se mostrará si falla la conexión
        )
        
        # Contenedor principal
        self.content = ft.Container(
            alignment=ft.alignment.center,
            width=400,
            height=500,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=0,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.GREY_400,
            ),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                controls=[
                    ft.Container(
                        width=80,
                        height=80,
                        border_radius=15,
                        bgcolor=ft.Colors.BLUE_GREY_600,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=5,
                            color="rgba(39, 245, 180, 0.15)",
                        ),
                        content=ft.Icon(
                            ft.Icons.MONITOR_HEART,
                            color=ft.Colors.WHITE,
                            size=55
                        )
                    ),
                    ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(
                                "Sistema de",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color="#2C3E50"
                            ),
                            ft.Text(
                                "Monitoreo y Registro",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_GREY_300
                            )
                        ]
                    ),
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    
                    # Estado de conexión
                    self.connection_container,
                    
                    ft.Text(
                        "Inicia sesión para continuar",
                        size=16,
                        color=ft.Colors.GREY_600,
                    ),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    self.login_button,
                    self.connection_details,
                    self.offline_button,
                ]
            )
        )
        
        # Iniciar conexión automáticamente
        self.iniciar_conexion()
    
    def iniciar_conexion(self):
        """Inicia la conexión a la base de datos en un hilo separado"""
        def attempt_connection():
            success, message = self.db.connect()
            
            def update_ui():
                self.connecting = False
                
                if success:
                    # Conexión exitosa
                    self.connection_spinner.color = ft.Colors.GREEN
                    self.connection_status = message
                    self.connection_color = ft.Colors.GREEN
                    
                    # Mostrar detalles de conexión
                    self.connection_details.visible = True
                    
                    # Habilitar botón de login
                    self.login_button.disabled = False
                    
                    # Cambiar estilo del spinner a éxito
                    self.connection_spinner.value = 1.0  # Completo
                else:
                    # Conexión fallida
                    self.connection_spinner.color = ft.Colors.RED
                    self.connection_status = message
                    self.connection_color = ft.Colors.RED
                    
                    # Habilitar botón de login (modo offline)
                    self.login_button.disabled = False
                    
                    # Mostrar botón para modo offline
                    self.offline_button.visible = True
                    
                    # Cambiar spinner a error
                    self.connection_spinner.value = 1.0  # Completo
                
                self.page.update()
            
            self.page.run_thread(update_ui)
        
        # Ejecutar en hilo separado
        threading.Thread(target=attempt_connection, daemon=True).start()
    
    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON"""
        if os.path.exists(self.usuarios_file):
            try:
                with open(self.usuarios_file, "r") as f:
                    datos = json.load(f)
                    self.usuarios = datos
            except:
                self.usuarios = {}
        else:
            self.usuarios = {} # Diccionario vacio
            # Crear usuario Administrador por defecto si no existe
            self.usuarios["Admin"] = {"password": "admin123", "rol": "Administrador"}
            self.usuarios["Operador"] = {"password": "operador123", "rol": "Operador"}
            self.guardar_usuarios()
    
    def guardar_usuarios(self):
        """Guarda los usuarios en el archivo JSON"""
        try:
            with open(self.usuarios_file, "w") as f:
                json.dump(self.usuarios, f, indent=2)
        except Exception as e:
            print(f"Error guardando usuarios: {e}")
    
    def verificar_login(self, e):
        """Verifica las credenciales del usuario"""
        if self.connecting:
            self.error_text.value = "Espere mientras se establece la conexión..."
            self.page.update()
            return
            
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        
        if not username or not password:
            self.error_text.value = "Por favor, completa todos los campos"
            self.page.update()
            return
        
        if username in self.usuarios and self.usuarios[username]["password"] == password:
            self.error_text.value = ""
            # Guardar sesión actual con rol
            self.usuario_actual = username
            self.rol_actual = self.usuarios[username]["rol"]
            
            # Llamar al callback de éxito con usuario, rol y conexión
            self.on_login_success(username, self.rol_actual, self.db)
        else:
            self.error_text.value = "Usuario y/o contraseña incorrectos"
            self.page.update()
    
    def use_offline_mode(self, e):
        """Usa el modo offline cuando no hay conexión"""
        # Cerrar conexión si estaba intentando
        self.db.close()
        
        # Actualizar estado
        self.connection_status = "Modo offline - Sin conexión a base de datos"
        self.connection_color = ft.Colors.ORANGE
        self.connection_spinner.color = ft.Colors.ORANGE
        self.connection_spinner.value = 1.0
        self.login_button.disabled = False
        
        # Habilitar campos
        self.username_field.disabled = False
        self.password_field.disabled = False
        
        self.page.update()

# ========== CLASE PARA INTERFAZ ==========
class UI(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__(expand=True, padding=10)
        self.page = page
        self.usuario_actual = None
        self.rol_actual = None
        self.db_connection = None
        self.local_mode = False

        # Variables para el ciclo de filas
        self.fila_actual = 0  # Índice de la fila actual
        self.total_filas = 0  # Total de filas disponibles
        self.ciclo_activo = True  # Control del ciclo
        self.intervalo_ciclo = 5  # Segundos entre cambios de fila
        
        # Variable para el badge de notificaciones
        self.notificacion_badge = None
        # Variable para saber si estamos en la página de Alertas
        self.en_pagina_alertas = False
        
        # Mostrar pantalla de login directamente
        self.mostrar_login()

    def mostrar_login(self):
        """Muestra la pantalla de inicio de sesión"""
        self.login_screen = LoginScreen(
            page=self.page,
            on_login_success=self.on_login_success
        )

        # Configurar la página para login
        self.page.clean()
        self.page.add(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                width=self.page.width,
                height=self.page.height,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.Colors.BLUE_GREY_100, ft.Colors.WHITE]
                ),
                content=ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.login_screen.content]
                )
            )
        )
        self.page.update()
    
    def on_login_success(self, username, rol, db_connection):
        """Se ejecuta cuando el login es exitoso"""
        self.usuario_actual = username
        self.rol_actual = rol
        self.db_connection = db_connection
        self.local_mode = not (self.db_connection and self.db_connection.is_connected)
        
        # Inicializar la aplicación principal
        self.inicializar_aplicacion()

    def crear_boton_alertas_con_badge(self):
        """Crea un botón de alertas con badge de notificaciones como controles separados"""
        
        # ========== BOTÓN PRINCIPAL ==========
        # Crear el botón simple (sin badge)
        boton_principal = ft.Container(
            content=ft.Icon(
                ft.Icons.NOTIFICATIONS,
                color=ft.Colors.BLUE_GREY_600,
                size=30,
            ),
            width=40,
            height=40,
            border_radius=20,
            alignment=ft.alignment.center,
            on_click=lambda e: self.change_page(2),
            tooltip="Alertas",
        )
        
        # ========== BADGE SEPARADO ==========
        # Crear badge como control
        self.notificacion_badge_text = ft.Text("0", size=10, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        
        self.notificacion_badge = ft.Container(
            width=20,
            height=20,
            border_radius=10,
            bgcolor=ft.Colors.RED_600,
            alignment=ft.alignment.center,
            visible=False,  # Inicialmente oculto
            border=ft.border.all(1, ft.Colors.WHITE),
            content=self.notificacion_badge_text,
            # Posicionamiento absoluto
            top=0,
            right=0,
        )
        
        # ========== CONTENEDOR QUE AGRUPA AMBOS ==========
        # Crear un Stack que contiene ambos controles pero mantiene sus identidades
        contenedor_combinado = ft.Stack(
            width=40,
            height=40,
            controls=[
                boton_principal,
                self.notificacion_badge
            ]
        )
        
        return contenedor_combinado

    def inicializar_aplicacion(self):
        """Inicializa la aplicación principal después del login"""
        self.page.clean()

        # Variables para datos en tiempo real
        self.datos_tiempo_real = {
            'presion-fel_1-09': 0,
            'presion-fel_2-09': 0,
            'presion-fel_3-09': 0,
            'presion-ng-09': 0,
            'temperatura-09': 0,
            'humedad-09': 0,
            'presion-24': 0,
            'presion-30': 0,
            'presion-35': 0,
            'presion-36': 0,
            'presion-50': 0,
            'presion-51': 0,
            'presion-52': 0,
            'presion-53': 0,
            'presion-54': 0,
            'presion-55': 0,
            'presion-56': 0,
            'presion-57': 0,
            'presion-58': 0,
            'presion-59': 0,
            'presion-60': 0,
            'presion-61': 0,
            'presion-62': 0,
            'presion-63': 0,
            'presion-64': 0,
            'presion-65': 0,
            'presion-66': 0,
            'presion-67': 0,
            'presion-68': 0,
            'presion-69': 0,
            'presion-70': 0,
            'presion-72': 0,
        }

        self.reloj_global = Reloj()
        self.sistema_alertas = SistemaAlertas()
        self.alertas_view = None

        self.color_main = ft.Colors.GREY_300

        self.iniciar_actualizacion_hora_visual()

        # Agregar barra de usuario en la parte superior
        self.barra_usuario = self.crear_barra_usuario()

        self.btn_connect3 = self.crear_boton_alertas_con_badge()
        
        self.inicializar_ui()

        self.reloj_global.agregar_callback(self.fnc_hr_alcanzada)

        self.inicializar_alertas_view()
        
        # Crear layout principal con barra de usuario
        layout_principal = ft.Column(
            expand=True,
            controls=[
                self.barra_usuario,
                ft.Container(
                    expand=True,
                    content=self.resp_container
                )
            ]
        )
        
        self.content = layout_principal
        
        # self.configurar_banner()
        # self.inicializar_alertas_view()

        # self.reloj_global.agregar_callback(self.fnc_hr_alcanzada)
        
        # Agregar a la página
        self.page.add(self)
        self.page.update()
    
    def iniciar_actualizacion_hora_visual(self):
        """ Solo actualiza la hora visual, no las alarmas """
        # ---------- TEXTO HORA ACTUAL ----------
        self.texto_hora = ft.Text(
            value="--:-- --",
            size=17,
            weight="bold",
            color=ft.Colors.WHITE,
        )
        
        def actualizar_hora():
            while True:
                try:
                    ahora = datetime.datetime.now()
                    if self.page:
                        def update_ui():
                            self.texto_hora.value = ahora.strftime("%I:%M:%S %p")
                            self.page.update()
                        self.page.run_thread(update_ui)
                    time.sleep(1)
                except:
                    break
        
        thread = threading.Thread(target=actualizar_hora, daemon=True)
        thread.start()
    
    def crear_barra_usuario(self):
        """Crea la barra superior con información del usuario"""
        # Determinar color según el rol
        rol_color = ft.Colors.ORANGE if self.rol_actual == "Administrador" else ft.Colors.GREEN
        rol_texto = "Administrador" if self.rol_actual == "Administrador" else "Operador"
        
        # Estado de conexión BD
        if self.db_connection and self.db_connection.is_connected:
            db_status = "✅ Conectado"
            db_color = ft.Colors.GREEN
        else:
            db_status = "❌ Sin conexión"
            db_color = ft.Colors.RED
        
        # Agregar texto de estado de fila
        self.texto_estado_fila = ft.Text(
            value="Fila: -/-",
            size=12,
            color=ft.Colors.WHITE70,
        )
        
        # Agregar controles de ciclo (solo si hay conexión)
        if self.db_connection and self.db_connection.is_connected:
            fila_controls = [
                ft.Row(
                    spacing=5,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.SKIP_PREVIOUS,
                            icon_size=16,
                            tooltip="Fila anterior",
                            on_click=lambda e: self.cambiar_fila(-1)
                        ),
                        self.texto_estado_fila,
                        ft.IconButton(
                            icon=ft.Icons.SKIP_NEXT,
                            icon_size=16,
                            tooltip="Siguiente fila",
                            on_click=lambda e: self.cambiar_fila(1)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PLAY_CIRCLE if not self.ciclo_activo else ft.Icons.PAUSE_CIRCLE,
                            icon_size=16,
                            tooltip="Pausar/Reanudar ciclo automático",
                            on_click=self.toggle_ciclo
                        )
                    ]
                )
            ]
        else:
            fila_controls = []
        
        return ft.Container(
            height=80,
            border_radius=10,
            bgcolor=ft.Colors.BLUE_GREY_600,
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Column(
                spacing=5,
                controls=[
                    # Primera fila: Usuario y hora
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=24),
                                    ft.Text(
                                        f"{self.usuario_actual}",
                                        color=ft.Colors.WHITE,
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            rol_texto,
                                            color=ft.Colors.WHITE,
                                            size=12,
                                        ),
                                        bgcolor=rol_color,
                                        padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                        border_radius=10,
                                    )
                                ]
                            ),
                            self.texto_hora
                        ]
                    ),
                    # Segunda fila: Estado de BD y controles de ciclo
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(
                                ft.Icons.DATA_EXPLORATION,
                                color=db_color,
                                size=16
                            ),
                            ft.Text(
                                f"Base de datos: {db_status}",
                                size=12,
                                color=db_color,
                                weight=ft.FontWeight.BOLD,
                            ),
                            *fila_controls  # Agregar controles de ciclo si existen
                        ]
                    )
                ]
            )
        )
    
    def cambiar_fila(self, delta):
        """Cambia manualmente a la siguiente/anterior fila"""
        if self.total_filas > 0:
            self.fila_actual = (self.fila_actual + delta) % self.total_filas
            # Actualizar el texto de estado
            self.texto_estado_fila.value = f"Fila: {self.fila_actual + 1}/{self.total_filas}"
            self.texto_estado_fila.update()
            # Actualizar datos inmediatamente
            self.actualizar_datos_desde_bd()
    
    def toggle_ciclo(self, e):
        """Activa/desactiva el ciclo automático"""
        self.ciclo_activo = not self.ciclo_activo
        e.control.icon = ft.Icons.PLAY_CIRCLE if not self.ciclo_activo else ft.Icons.PAUSE_CIRCLE
        e.control.update()
    
    def actualizar_datos_desde_bd(self):
        """Fuerza una actualización inmediata de los datos desde la BD"""
        if self.db_connection and self.db_connection.is_connected:
            try:
                datos, mensaje, total_filas = self.db_connection.get_all_data(self.fila_actual)
                if datos:
                    self.datos_tiempo_real = datos
                    # Actualizar UI
                    self.actualizar_ui_con_datos(datos, f"Manual: {mensaje}")
                    print(f"📊 Datos actualizados manualmente: {mensaje}")
            except Exception as e:
                print(f"❌ Error actualizando datos: {e}")

    def cerrar_sesion(self, e):
        """Cierra la sesión actual y vuelve al login"""
        # Cerrar conexión a la base de datos si existe
        if self.db_connection:
            self.db_connection.close()
        
        # Limpiar variables
        self.usuario_actual = None
        self.rol_actual = None
        self.db_connection = None
        
        # Volver a mostrar el login
        self.mostrar_login()

    def inicializar_alertas_view(self):
        """Inicializa AlertasView después de que todo esté listo"""

        self.alertas_view = AlertasView(self.sistema_alertas)
        self.actualizar_alertas_container()

        # Inicializar el contador de alertas DESPUÉS de que la página esté lista
        self.page.run_thread(self.inicializar_contador_alertas)
    
    def inicializar_contador_alertas(self):
        """Inicializa el contador de alertas después de que la página esté lista"""
        time.sleep(0.5)
        self.actualizar_contador_alertas()

    def actualizar_alertas_container(self):
        """Actualiza el contenedor de alertas con el AlertasView"""
        if self.alertas_view is None:
            return
        
        # ==================== CONTENEDOR DE LA PANTALLA DE ALERTAS ====================
        """ Componentes que conforman la seccion de alertas """
        self.alertas_container_1.content = ft.Column(
            controls=[
                ft.Container(
                    border_radius=20,
                    alignment=ft.alignment.center,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                border_radius=20,
                                expand=True,
                                alignment=ft.alignment.center,
                                content=ft.Text("Historial de alertas del sistema",
                                    font_family="Univers",
                                    size=30,
                                    weight=ft.FontWeight.BOLD,
                                )
                            ),
                            ft.Container(
                                height=35,
                                width=35,
                                border_radius=20,
                                alignment=ft.alignment.center,
                                content=
                                ft.Icon(
                                    ft.Icons.SETTINGS,
                                    color=ft.Colors.BLUE_GREY_600,
                                    size=30,
                                ),
                                tooltip="Configuración",
                                on_click = lambda e: self.change_page(3)
                            )
                        ]
                    )
                ),
                ft.Container(
                    expand=True,
                    bgcolor=self.color_main,
                    border_radius=10,
                    padding=10,
                    content=self.alertas_view
                )
            ]
        )

    def registrar_manual(self, hora):
        """ Se ejecuta cuando el reloj global detecta una alarma """
        print("\n")
        print("=" * 100)

        # Obtener datos actuales de la fila activa
        datos = self.datos_tiempo_real.copy()

        # Obtener hora actual
        hora_actual = datetime.datetime.now().strftime("%I:%M %p")

        # Intentar guardar en base de datos si hay conexión
        if self.db_connection and self.db_connection.is_connected:
            try:
                # Actualizar datos en las tablas correspondientes
                self.db_connection.insert_pressure_data(datos)
                self.db_connection.insert_uma_data(datos)
                print("✅ Datos actualizados en base de datos")
            except Exception as e:
                print(f"❌ Error guardando en base de datos: {e}")

        registro = self.reloj_global.agregar_al_historial(
            datos, 
            tipo="Manual", 
            fuente=f"UMA 09 {hora_actual} - Fila {self.fila_actual + 1}"
        )

        self.agregar_alerta_y_actualizar(
            causa=f"Registro manual ejecutado (Fila {self.fila_actual + 1})",
            pagina="UMA 09",
            elemento="(Botón)"
        )
        
        # FORZAR ACTUALIZACIÓN DE UMA INMEDIATAMENTE
        if hasattr(self, 'uma_instance'):
            self.page.run_thread(lambda: self.uma_instance.actualizar_lista())
            print("Si entra a la funcion para actualizar lista")
        
        else:
            print("Error al intentar actualizar")

        
        # # Si estamos en la página de gráficas, actualizar
        # if self.container_1.content == self.grafica_container and self.manometro_numero is not None:
        #     self.page.run_thread(self.actualizar_historial_manometro)
        
        self.mostrar_notificacion(mensaje=f"Registro manual completado (Fila {self.fila_actual + 1})", color=ft.Colors.GREEN_100)
    
    def mostrar_notificacion(self, mensaje, color):
        """Muestra una notificación temporal"""
        try:
            # Crear snackbar
            snackbar = ft.SnackBar(
                content=ft.Text(mensaje, color=ft.Colors.BLACK),
                bgcolor=color,
                duration=3000,
            )

            self.page.overlay.append(snackbar)
            snackbar.open = True
            self.page.update()

        except Exception as e:
            print("Error mostrando SnackBar")

    # ---------- FUNCION QUE SE EJECUTA AL LLEGAR LA HORA DE REGISTRO ----------
    def fnc_hr_alcanzada(self, hora):
        """ Se ejecuta cuando el reloj global detecta una alarma """
        print("\n")
        print("=" * 100)

        # Obtener datos actuales de la fila activa
        datos = self.datos_tiempo_real.copy()

        # Intentar guardar en base de datos si hay conexión
        if self.db_connection and self.db_connection.is_connected:
            try:
                # Actualizar datos en las tablas correspondientes
                self.db_connection.insert_pressure_data(datos)
                self.db_connection.insert_uma_data(datos)
                print("✅ Datos actualizados en base de datos automáticamente")
            except Exception as e:
                print(f"❌ Error guardando en base de datos: {e}")

        registro = self.reloj_global.agregar_al_historial(
            datos, 
            tipo="Automatico", 
            fuente=f"Alarma {hora} - Fila {self.fila_actual + 1}"
        )

        self.agregar_alerta_y_actualizar(
            causa=f"Registro automático ejecutado (Fila {self.fila_actual + 1})",
            pagina="Configuracion",
            elemento="(Reloj)",
        )
        
        # FORZAR ACTUALIZACIÓN DE UMA INMEDIATAMENTE
        if hasattr(self, 'uma_instance'):
            self.page.run_thread(lambda: self.uma_instance.actualizar_lista())
            print("Si entra a la funcion para actualizar lista")
        
        else:
            print("Error al intentar actualizar")
        
        # # Si estamos en la página de gráficas, actualizar
        # if self.container_1.content == self.grafica_container and self.manometro_numero is not None:
        #     self.page.run_thread(self.actualizar_historial_manometro)
        
        self.mostrar_notificacion(mensaje=f"Registro automático completado (Fila {self.fila_actual + 1})", color=ft.Colors.BLUE_100)
    
    def agregar_alerta_y_actualizar(self, causa, pagina, elemento):
        """Agrega una alerta y actualiza la vista y el contador"""
        # Agregar la alerta al sistema
        self.sistema_alertas.agregar_alerta(causa, pagina, elemento)

        # Actualizar el contador de notificaciones
        self.actualizar_contador_alertas()
        
        # Notificar a AlertasView si está en la página actual
        if self.alertas_view is not None and hasattr(self.alertas_view, 'en_pagina') and self.alertas_view.en_pagina:
            self.page.run_thread(self.alertas_view.cargar_ui)
            print(f"Alerta agregada y vista actualizada: {causa}")

    # ---------- FUNCIONES UI ----------

    def Check_On_Hover(self, e):
        ctrl = e.control 

        is_hover = (e.data == "true" or e.data is True)

        if is_hover:
            ctrl.border = ft.border.all(3, ft.Colors.BLUE_GREY_600)
            ctrl.border_radius = 40
            ctrl.scale = ft.Scale(1.08)
        else:
            ctrl.border = ft.border.all(3, ft.Colors.GREY_600)
            ctrl.border_radius = 10
            ctrl.scale = ft.Scale(1)

        ctrl.update()

    def Check_On_Click(self, e):
        ctrl = e.control 

        ctrl.scale = ft.Scale(0.95)
        ctrl.update()
        time.sleep(0.1)
        ctrl.scale = ft.Scale(1)
        ctrl.update()

        if ctrl.data == 0: # Pantalla (UMA 09)
            self.change_page(0)
        elif ctrl.data == 1: # Pantalla (TM)
            self.change_page(1)
        elif ctrl.data == 2: # Pantalla (Alertas)
            self.change_page(4)

    def change_page(self, index):
        """Cambia entre páginas de la aplicación"""
        self.container_1.content = self.container_list_1[index]
        # self.actualizar_colores_botones(index)
        
        # Actualizar estado de la página de Alertas
        if index == 2:  # Si estamos entrando a Alertas
            self.en_pagina_alertas = True
            # Ocultar el badge
            if self.notificacion_badge is not None:
                self.notificacion_badge.visible = False
                try:
                    self.notificacion_badge.update()
                except:
                    pass
        else:  # Si estamos saliendo de Alertas
            self.en_pagina_alertas = False
            # Actualizar el contador para que se muestre si hay alertas
            self.actualizar_contador_alertas()
        
        # Si estamos entrando a la página de gráficas, actualizar datos
        if index == 4 and hasattr(self, 'manometro_activo') and hasattr(self, 'manometro_numero'):
            if self.manometro_numero:
                self.page.run_thread(self.actualizar_historial_manometro)
        
        if self.alertas_view is not None:
            if index == 2:  # Alertas está en índice 2
                if hasattr(self.alertas_view, 'entrar_a_pagina'):
                    self.alertas_view.entrar_a_pagina()
            else:
                if hasattr(self.alertas_view, 'salir_de_pagina'):
                    self.alertas_view.salir_de_pagina()

        self.page.update()

    def actualizar_colores_botones(self, index_activo):
        """Actualiza los colores de los botones de navegación"""
        botones = [self.btn_UMA_09, self.btn_TM_01]
        
        for i, btn in enumerate(botones):
            if i == index_activo:
                btn.bgcolor = ft.Colors.BLUE_GREY_600
                btn.scale = ft.Scale(0.95)
                btn.update()
                time.sleep(0.1)
                btn.scale = ft.Scale(1)
                btn.update()
                btn.disabled=True
            else:
                btn.disabled=False
                btn.update()

    def iniciar_actualizacion_desde_db(self):
        """Inicia la actualización de datos desde la base de datos con ciclo"""
        def loop():
            update_count = 0
            ultimo_cambio = time.time()
            
            while True:
                datos = {}
                source = "Local"
                
                # Determinar si es momento de cambiar de fila
                tiempo_actual = time.time()
                if tiempo_actual - ultimo_cambio >= self.intervalo_ciclo:
                    if self.ciclo_activo and self.total_filas > 1:
                        self.fila_actual = (self.fila_actual + 1) % self.total_filas
                        ultimo_cambio = tiempo_actual
                
                # Intentar obtener datos de BD si hay conexión
                if self.db_connection and self.db_connection.is_connected:
                    try:
                        datos, mensaje, total_filas = self.db_connection.get_all_data(self.fila_actual)
                        if datos:
                            source = f"SQL Server - {mensaje}"
                            self.total_filas = total_filas
                            # print(f"📊 {source}")
                        else:
                            # Si no hay datos en BD, mostrar valores vacíos
                            datos = self.get_datos_vacios()
                            source = "Sin datos en BD"
                    except Exception as e:
                        print(f"❌ Error obteniendo datos de BD: {e}")
                        datos = self.get_datos_vacios()
                        source = "Error BD"
                else:
                    # Si no hay conexión, mostrar valores vacíos
                    datos = self.get_datos_vacios()
                    source = "Sin conexión"
                
                def actualizar():
                    # Actualizar el indicador de fila en la interfaz si hay conexión
                    if self.db_connection and self.db_connection.is_connected and self.total_filas > 0:
                        self.texto_estado_fila.value = f"Fila: {self.fila_actual + 1}/{self.total_filas}"
                        self.texto_estado_fila.update()
                    
                    # Actualizar UI con los datos
                    self.actualizar_ui_con_datos(datos, source)
                    
                    # Actualizar también la página de gráficas si estamos en ella
                    if (hasattr(self, 'manometro_activo') and 
                        hasattr(self, 'presion_actual_display') and
                        self.container_1.content == self.grafica_container and
                        hasattr(self, 'manometro_numero') and self.manometro_numero):
                        
                        # Obtener el valor directamente
                        clave_presion = f'presion-{self.manometro_numero}'
                        if clave_presion in datos:
                            valor = datos[clave_presion]
                            if valor == 0 and source == "Sin conexión":
                                self.presion_actual_display.value = "-- Pa"
                            else:
                                self.presion_actual_display.value = f"{valor:.1f} Pa"

                    # Log periódico solo si hay conexión
                    nonlocal update_count
                    update_count += 1
                    if update_count % 10 == 0 and source != "Sin conexión":
                        print(f"🔄 Actualización #{update_count} ({source})")
                    
                    self.page.update()
                
                self.page.run_thread(actualizar)
                time.sleep(1)  # Actualizar cada segundo
        
        threading.Thread(target=loop, daemon=True).start()
    
    def actualizar_ui_con_datos(self, datos, source):
        """Actualiza la UI con los datos proporcionados"""
        # UMA - Actualizar con datos obtenidos
        self.txt_temp_09.value = f"{datos.get('temperatura-09', 0):.1f} °C" if datos.get('temperatura-09', 0) != 0 else "-- °C"
        self.txt_hum_09.value = f"{datos.get('humedad-09', 0):.1f} %" if datos.get('humedad-09', 0) != 0 else "-- %"
        self.txt_pres_fel_1_09.value = f"{datos.get('presion-fel_1-09', 0):.1f} Pa" if datos.get('presion-fel_1-09', 0) != 0 else "-- Pa"
        self.txt_pres_fel_2_09.value = f"{datos.get('presion-fel_2-09', 0):.1f} Pa" if datos.get('presion-fel_2-09', 0) != 0 else "-- Pa"
        self.txt_pres_fel_3_09.value = f"{datos.get('presion-fel_3-09', 0):.1f} Pa" if datos.get('presion-fel_3-09', 0) != 0 else "-- Pa"
        self.txt_pres_fel_ng_09.value = f"{datos.get('presion-ng-09', 0):.1f} Pa" if datos.get('presion-ng-09', 0) != 0 else "-- Pa"
        
        # Presión - Actualizar con datos obtenidos
        presion_keys = ['presion-24', 'presion-30', 'presion-35', 'presion-36',
                       'presion-50', 'presion-51', 'presion-52', 'presion-53',
                       'presion-54', 'presion-55', 'presion-56', 'presion-57',
                       'presion-58', 'presion-59', 'presion-60', 'presion-61',
                       'presion-62', 'presion-63', 'presion-64', 'presion-65',
                       'presion-66', 'presion-67', 'presion-68', 'presion-69',
                       'presion-70', 'presion-72']
        
        # Obtener todos los controles de texto de presión
        presion_controls = [
            self.txt_pres_m_24_09, self.txt_pres_m_30_09, self.txt_pres_m_35_09, self.txt_pres_m_36_09,
            self.txt_pres_m_50_09, self.txt_pres_m_51_09, self.txt_pres_m_52_09, self.txt_pres_m_53_09,
            self.txt_pres_m_54_09, self.txt_pres_m_55_09, self.txt_pres_m_56_09, self.txt_pres_m_57_09,
            self.txt_pres_m_58_09, self.txt_pres_m_59_09, self.txt_pres_m_60_09, self.txt_pres_m_61_09,
            self.txt_pres_m_62_09, self.txt_pres_m_63_09, self.txt_pres_m_64_09, self.txt_pres_m_65_09,
            self.txt_pres_m_66_09, self.txt_pres_m_67_09, self.txt_pres_m_68_09, self.txt_pres_m_69_09,
            self.txt_pres_m_70_09, self.txt_pres_m_72_09
        ]
        
        # Actualizar cada control
        for i, key in enumerate(presion_keys):
            valor = datos.get(key, 0)
            if valor == 0 and source == "Sin conexión":
                presion_controls[i].value = "-- Pa"
            else:
                presion_controls[i].value = f"{valor:.1f} Pa"

        # Actualizar datos en tiempo real
        self.datos_tiempo_real = datos

        # Verificar condiciones para alertas
        self.verificar_alertas(datos)

    def get_datos_vacios(self):
        """Retorna datos vacíos cuando no hay conexión"""
        return {
            "temperatura-09": 0, "humedad-09": 0,
            "presion-fel_1-09": 0, "presion-fel_2-09": 0, 
            "presion-fel_3-09": 0, "presion-ng-09": 0,
            "presion-24": 0, 'presion-30': 0, 'presion-35': 0, 
            'presion-36': 0, 'presion-50': 0, 'presion-51': 0, 
            'presion-52': 0, 'presion-53': 0, 'presion-54': 0, 
            'presion-55': 0, 'presion-56': 0, 'presion-57': 0,
            'presion-58': 0, 'presion-59': 0, 'presion-60': 0, 
            'presion-61': 0, 'presion-62': 0, 'presion-63': 0,
            'presion-64': 0, 'presion-65': 0, 'presion-66': 0,
            'presion-67': 0, 'presion-68': 0, 'presion-69': 0,
            'presion-70': 0, 'presion-72': 0,
        }
    
    def verificar_alertas(self, datos):
        """Verifica condiciones para generar alertas"""
        # Temperatura (18 a 25 °C)
        temp_sol_09 = datos.get('temperatura-09', 0)
        if temp_sol_09 != 0 and (temp_sol_09 < 18 or temp_sol_09 > 25):
            self.agregar_alerta_y_actualizar(
                causa=f"Temperatura fuera de especificación: {temp_sol_09} °C (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(Tem. Ret.)"
            )
        
        # Humedad (30 a 65 %)
        hum_sol_09 = datos.get('humedad-09', 0)
        if hum_sol_09 != 0 and (hum_sol_09 < 30 or hum_sol_09 > 65):
            self.agregar_alerta_y_actualizar(
                causa=f"Humedad fuera de especificación: {hum_sol_09} % (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(Hum. Ret.)"
            )
        
        # Presión M-COM-177 (24) (-25 a -13 Pa)
        pres_24_sol_09 = datos.get('presion-24', 0)
        if pres_24_sol_09 != 0 and (pres_24_sol_09 < -25 or pres_24_sol_09 > -13):
            self.agregar_alerta_y_actualizar(
                causa=f"Presion fuera de especificación: {pres_24_sol_09} Pa (Fila {self.fila_actual + 1})",
                pagina="TM-SOL",
                elemento="(M-COM-177)"
            )
        
        # Verificar presiones FEL y NG
        fel_1 = datos.get('presion-fel_1-09', 0)
        fel_2 = datos.get('presion-fel_2-09', 0)
        fel_3 = datos.get('presion-fel_3-09', 0)
        fel_ng = datos.get('presion-ng-09', 0)
        
        if fel_1 != 0 and fel_1 > 150:
            self.agregar_alerta_y_actualizar(
                causa=f"Presión FEL 1 excede límite: {fel_1} Pa (Max: 150 Pa) (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(FEL 1)"
            )
        
        if fel_2 != 0 and fel_2 > 300:
            self.agregar_alerta_y_actualizar(
                causa=f"Presión FEL 2 excede límite: {fel_2} Pa (Max: 300 Pa) (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(FEL 2)"
            )
        
        if fel_3 != 0 and fel_3 > 450:
            self.agregar_alerta_y_actualizar(
                causa=f"Presión FEL 3 excede límite: {fel_3} Pa (Max: 450 Pa) (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(FEL 3)"
            )
        
        if fel_ng != 0 and fel_ng > 600:
            self.agregar_alerta_y_actualizar(
                causa=f"Presión NG excede límite: {fel_ng} Pa (Max: 600 Pa) (Fila {self.fila_actual + 1})",
                pagina="UMA 09",
                elemento="(NG)"
            )
        
        # Puedes agregar más verificaciones para otros manómetros aquí
    
    def redondear_entero_desde_6(self, valor):
        """Redondea hacia arriba desde 0.6"""
        parte_entera = int(valor)
        decimal = valor - parte_entera
        return parte_entera + 1 if decimal >= 0.6 else parte_entera
    
    def abrir_pagina_grafica(self, titulo_manometro):
        """Abre la página de gráficas para un manómetro específico"""
        print(f"Abriendo gráfica para: {titulo_manometro}")
        
        # 1. Guardar referencia al manómetro activo
        self.manometro_activo = titulo_manometro
        
        # 2. Obtener datos del manómetro específico
        if "M-COM-177" in titulo_manometro:
            self.manometro_numero = 24
            datos = self.datos_tiempo_real['presion-24']
        elif "M-COM-182" in titulo_manometro:
            self.manometro_numero = 30
            datos = self.datos_tiempo_real['presion-30']
        elif "M-COM-186" in titulo_manometro:
            self.manometro_numero = 35
            datos = self.datos_tiempo_real['presion-35']
        elif "M-COM-187" in titulo_manometro:
            self.manometro_numero = 36
            datos = self.datos_tiempo_real['presion-36']
        elif "M-COM-201" in titulo_manometro:
            self.manometro_numero = 50
            datos = self.datos_tiempo_real['presion-50']
        elif "M-COM-202" in titulo_manometro:
            self.manometro_numero = 51
            datos = self.datos_tiempo_real['presion-51']
        elif "M-COM-203" in titulo_manometro:
            self.manometro_numero = 52
            datos = self.datos_tiempo_real['presion-52']
        elif "M-COM-204" in titulo_manometro:
            self.manometro_numero = 53
            datos = self.datos_tiempo_real['presion-53']
        elif "M-COM-205" in titulo_manometro:
            self.manometro_numero = 54
            datos = self.datos_tiempo_real['presion-54']
        elif "M-COM-206" in titulo_manometro:
            self.manometro_numero = 55
            datos = self.datos_tiempo_real['presion-55']
        elif "M-COM-227" in titulo_manometro:
            self.manometro_numero = 56
            datos = self.datos_tiempo_real['presion-56']
        elif "M-COM-228" in titulo_manometro:
            self.manometro_numero = 57
            datos = self.datos_tiempo_real['presion-57']
        elif "M-COM-229" in titulo_manometro:
            self.manometro_numero = 58
            datos = self.datos_tiempo_real['presion-58']
        elif "M-COM-230" in titulo_manometro:
            self.manometro_numero = 59
            datos = self.datos_tiempo_real['presion-59']
        elif "M-COM-231" in titulo_manometro:
            self.manometro_numero = 60
            datos = self.datos_tiempo_real['presion-60']
        elif "M-COM-232" in titulo_manometro:
            self.manometro_numero = 61
            datos = self.datos_tiempo_real['presion-61']
        elif "M-COM-233" in titulo_manometro:
            self.manometro_numero = 62
            datos = self.datos_tiempo_real['presion-62']
        elif "M-COM-234" in titulo_manometro:
            self.manometro_numero = 63
            datos = self.datos_tiempo_real['presion-63']
        elif "M-COM-235" in titulo_manometro:
            self.manometro_numero = 64
            datos = self.datos_tiempo_real['presion-64']
        elif "M-COM-236" in titulo_manometro:
            self.manometro_numero = 65
            datos = self.datos_tiempo_real['presion-65']
        elif "M-COM-237" in titulo_manometro:
            self.manometro_numero = 66
            datos = self.datos_tiempo_real['presion-66']
        elif "M-COM-238" in titulo_manometro:
            self.manometro_numero = 67
            datos = self.datos_tiempo_real['presion-67']
        elif "M-COM-239" in titulo_manometro:
            self.manometro_numero = 68
            datos = self.datos_tiempo_real['presion-68']
        elif "M-COM-240" in titulo_manometro:
            self.manometro_numero = 69
            datos = self.datos_tiempo_real['presion-69']
        elif "M-COM-241" in titulo_manometro:
            self.manometro_numero = 70
            datos = self.datos_tiempo_real['presion-70']
        elif "M-COM-243" in titulo_manometro:
            self.manometro_numero = 72
            datos = self.datos_tiempo_real['presion-72']
        else:
            self.manometro_numero = None
            datos = 0
        
        # 3. Actualizar el título de la página
        self.titulo_grafica_text.value = f"Gráfica del manómetro: {titulo_manometro}"
        
        # 4. Actualizar el valor inicial en el display
        if datos == 0 and (self.db_connection is None or not self.db_connection.is_connected):
            self.presion_actual_display.value = "-- Pa"
        else:
            self.presion_actual_display.value = f"{datos} Pa"
        
        # 5. Cambiar a la página de gráficas (índice 4)
        self.change_page(4) # Indice de la pagina de graficos.
        
        # 6. Actualizar historial y gráfica
        self.page.run_thread(self.actualizar_historial_manometro)
        
        # 7. Imprimir confirmación
        print(f"✓ Página de gráficas abierta para {titulo_manometro}")
        print(f"  Presión actual: {datos} Pa")
        print(f"  Número de manómetro: {self.manometro_numero}")
    
    def crear_punto_grafica(self, x, y):
        """Crea un punto de datos para la gráfica CON PUNTO VISIBLE"""
        return ft.LineChartDataPoint(
            x,
            y,
            selected_below_line=ft.ChartPointLine(
                width=0.5, color=ft.Colors.GREY_400, dash_pattern=[2, 4]
            ),
            selected_point=ft.ChartCirclePoint(
                stroke_width=2, 
                color=ft.Colors.BLUE_700,
                radius=6,  # Punto más grande
            ),
        )
    
    def actualizar_historial_manometro(self, e=None):
        """Actualiza la gráfica y la lista de historial para el manómetro activo"""
        if not hasattr(self, 'manometro_activo') or not hasattr(self, 'manometro_numero'):
            print("No hay manómetro activo")
            return
        
        if not self.manometro_activo or not self.manometro_numero:
            print("No hay manómetro activo")
            return
        
        print(f"Actualizando historial para manómetro {self.manometro_numero}")
        
        # DEFINIR LÍMITES DIFERENTES PARA CADA MANÓMETRO
        if self.manometro_numero == 24:
            limite_superior = -14
            limite_inferior = -24
        elif self.manometro_numero == 30:
            limite_superior = -23
            limite_inferior = -33
        elif self.manometro_numero == 35:
            limite_superior = 23
            limite_inferior = 13
        elif self.manometro_numero == 36:
            limite_superior = 17
            limite_inferior = 7
        elif self.manometro_numero == 50:
            limite_superior = -13
            limite_inferior = -23
        elif self.manometro_numero == 51:
            limite_superior = -20
            limite_inferior = -30
        elif self.manometro_numero == 52:
            limite_superior = -17
            limite_inferior = -27
        elif self.manometro_numero == 53:
            limite_superior = -10
            limite_inferior = -20
        elif self.manometro_numero == 54:
            limite_superior = -7
            limite_inferior = -17
        elif self.manometro_numero == 55:
            limite_superior = -6
            limite_inferior = -16
        elif self.manometro_numero == 56:
            limite_superior = -10
            limite_inferior = -20
        elif self.manometro_numero == 57:
            limite_superior = -14
            limite_inferior = -24
        elif self.manometro_numero == 58:
            limite_superior = -11
            limite_inferior = -21
        elif self.manometro_numero == 59:
            limite_superior = -10
            limite_inferior = -20
        elif self.manometro_numero == 60:
            limite_superior = -13
            limite_inferior = -23
        elif self.manometro_numero == 61:
            limite_superior = -16
            limite_inferior = -26
        elif self.manometro_numero == 62:
            limite_superior = -15
            limite_inferior = -25
        elif self.manometro_numero == 63:
            limite_superior = -15
            limite_inferior = -25
        elif self.manometro_numero == 64:
            limite_superior = -15
            limite_inferior = -25
        elif self.manometro_numero == 65:
            limite_superior = -15
            limite_inferior = -25
        elif self.manometro_numero == 66:
            limite_superior = -15
            limite_inferior = -25
        elif self.manometro_numero == 67:
            limite_superior = -10
            limite_inferior = -20
        elif self.manometro_numero == 68:
            limite_superior = -20
            limite_inferior = -30
        elif self.manometro_numero == 69:
            limite_superior = -22
            limite_inferior = -32
        elif self.manometro_numero == 70:
            limite_superior = -14
            limite_inferior = -24
        elif self.manometro_numero == 72:
            limite_superior = -16
            limite_inferior = -26
        else:
            limite_superior = 108
            limite_inferior = 80
        
        # ACTUALIZAR LEYENDA CON LOS LÍMITES
        self.actualizar_leyenda_limites(limite_superior, limite_inferior)
        
        # Obtener registros del manómetro desde el historial principal
        registros = self.reloj_global.obtener_registros_por_manometro(
            self.manometro_numero, 
            limite=31
        )
        
        # Actualizar contador
        self.contador_registros.value = f"{len(registros)} registros"
        
        # Limpiar gráfica actual
        puntos_grafica = []
        puntos_limite_superior = []
        puntos_limite_inferior = []
        
        if registros:
            # Crear etiquetas para el eje X (fechas)
            etiquetas_x = []
            
            # Agregar puntos a la gráfica (X = timestamp, Y = presión)
            for i, registro in enumerate(registros):
                timestamp = registro['fecha_hora'].timestamp()
                
                # Punto de datos
                punto = self.crear_punto_grafica(timestamp, registro['presion'])
                puntos_grafica.append(punto)
                
                # Punto para línea de límite superior
                punto_superior = ft.LineChartDataPoint(timestamp, limite_superior)
                puntos_limite_superior.append(punto_superior)
                
                # Punto para línea de límite inferior
                punto_inferior = ft.LineChartDataPoint(timestamp, limite_inferior)
                puntos_limite_inferior.append(punto_inferior)
                
                # Crear etiqueta para el eje X (fecha corta)
                fecha_corta = registro['fecha_hora'].strftime("%d/%m/%y\n%H:%M")
                etiquetas_x.append(ft.ChartAxisLabel(
                    value=timestamp,
                    label=ft.Text(fecha_corta, size=10)
                ))
            
            # Configurar eje X con las etiquetas de fecha
            self.grafica_chart.bottom_axis = ft.ChartAxis(
                labels=etiquetas_x,
                labels_size=35,
                labels_interval=1 if len(etiquetas_x) <= 10 else 2,
                title=ft.Text("Fecha y Hora", size=12)
            )
            
            # Configurar rango Y dinámico considerando los límites
            presiones = [r['presion'] for r in registros]
            min_presion = min(presiones) if presiones else limite_inferior
            max_presion = max(presiones) if presiones else limite_superior
            
            # Agregar margen para que se vean bien los límites
            self.grafica_chart.min_y = min(limite_inferior - 10, min_presion - 10)
            self.grafica_chart.max_y = max(limite_superior + 10, max_presion + 10)
            
            # Actualizar línea de la gráfica principal
            self.linea_grafica.data_points = puntos_grafica
            self.linea_grafica.curved = False
            self.linea_grafica.point=True
            
            # Actualizar línea de límite superior
            self.linea_limite_superior.data_points = puntos_limite_superior
            self.linea_limite_superior.curved = False
            
            # Actualizar línea de límite inferior
            self.linea_limite_inferior.data_points = puntos_limite_inferior
            self.linea_limite_inferior.curved = False
            
            # Agregar todas las líneas a la gráfica
            self.grafica_chart.data_series = [
                self.linea_grafica,
                self.linea_limite_superior,
                self.linea_limite_inferior
            ]
        else:
            # Si no hay registros, solo mostrar líneas de límite
            self.grafica_chart.data_series = [
                self.linea_limite_superior,
                self.linea_limite_inferior
            ]
        
        # Limpiar lista actual
        self.lista_historial_grafica.controls.clear()
        
        # Agregar registros a la lista (más reciente primero)
        for registro in reversed(registros):  # Invertir para mostrar más reciente arriba
            # Determinar color según tipo
            if "Automatico" in registro['tipo']:
                color_fondo = ft.Colors.GREEN_50
                bgcolor2 = ft.Colors.LIGHT_BLUE_ACCENT_100
                tipo_texto = "AUTO"
            elif "Manual" in registro['tipo']:
                color_fondo = ft.Colors.GREEN_50
                bgcolor2 = ft.Colors.LIGHT_GREEN_ACCENT_100
                tipo_texto = "MANUAL"
            else:
                color_fondo = ft.Colors.GREY_50
                bgcolor2 = ft.Colors.GREY_100
                tipo_texto = "OTRO"
            
            # Determinar si está por encima del límite
            sobre_limite = registro['presion'] > limite_superior
            debajo_limite = registro['presion'] < limite_inferior
            
            # Crear fila para la tabla
            fila = ft.Container(
                padding=10,
                expand=True,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.RED_50 if sobre_limite or debajo_limite else color_fondo,
                border_radius=5,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        # Presión
                        ft.Container(
                            width=60,
                            alignment=ft.alignment.center,
                            content=ft.Text(
                                f"{registro['presion']} Pa",
                                size=12,
                                color=ft.Colors.RED_700 if sobre_limite or debajo_limite else ft.Colors.BLACK,
                                weight=ft.FontWeight.BOLD
                            )
                        ),
                        # Fecha
                        ft.Container(
                            width=65,
                            # bgcolor="pink",
                            alignment=ft.alignment.center,
                            content=ft.Text(
                                registro['fecha'],
                                size=12,
                                color=ft.Colors.GREY_700
                            )
                        ),
                        # Hora
                        ft.Container(
                            width=65,
                            alignment=ft.alignment.center,
                            content=ft.Text(
                                registro['hora'],
                                size=12,
                                color=ft.Colors.GREY_700
                            )
                        ),
                        # Tipo
                        ft.Container(
                            width=50,
                            alignment=ft.alignment.center,
                            content=ft.Row(
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Container(
                                        height=20,
                                        width=50,
                                        alignment=ft.alignment.center,
                                        bgcolor=bgcolor2,
                                        border_radius=5,
                                        content=ft.Text(
                                            tipo_texto,
                                            size=6.5,
                                            weight=ft.FontWeight.BOLD
                                        )
                                    )
                                ]
                            )
                        )
                    ]
                )
            )
            
            self.lista_historial_grafica.controls.append(fila)
        
        # Si no hay registros, mostrar mensaje
        if not registros:
            self.lista_historial_grafica.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(ft.Icons.HISTORY, size=48, color=ft.Colors.GREY_400),
                            ft.Text(
                                "No hay registros históricos",
                                size=14,
                                color=ft.Colors.GREY_500
                            )
                        ]
                    )
                )
            )
        
        # Actualizar todos los componentes
        try:
            self.grafica_chart.update()
            self.lista_historial_grafica.update()
            self.contador_registros.update()
            self.presion_actual_display.update()
        except Exception as e:
            print(f"Error actualizando componentes: {e}")
    
    def actualizar_leyenda_limites(self, limite_superior, limite_inferior):
        """Actualiza la leyenda con los límites específicos del manómetro"""
        # Actualizar los textos de la leyenda
        self.leyenda_superior_text.value = f"Límite superior ({limite_superior} Pa)"
        self.leyenda_inferior_text.value = f"Límite inferior ({limite_inferior} Pa)"
        
        # Actualizar los componentes
        try:
            self.leyenda_superior_text.update()
            self.leyenda_inferior_text.update()
        except Exception as e:
            print(f"Error actualizando leyenda: {e}")
        
        print(f"Límites actualizados: Superior={limite_superior} Pa, Inferior={limite_inferior} Pa")

    # ---------- FUNCION PARA CREAR LOS COMPONENTES DE LA INTERFAZ ----------
    def inicializar_ui(self):

        self.titulo_patalla="UMA 09"

        # Controles de texto para UMA
        self.txt_pres_fel_1_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_fel_2_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_fel_3_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_fel_ng_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_temp_09 = ft.Text("-- °C", size=20, weight=ft.FontWeight.BOLD)
        self.txt_hum_09 = ft.Text("-- %", size=20, weight=ft.FontWeight.BOLD)

        # Crear UMA
        self.uma_instance = ContenedorUMA(
            Val_Tem=self.txt_temp_09,
            Val_Hum=self.txt_hum_09,
            Val_Fel_1=self.txt_pres_fel_1_09,
            Val_Fel_2=self.txt_pres_fel_2_09,
            Val_Fel_3=self.txt_pres_fel_3_09,
            Val_NG=self.txt_pres_fel_ng_09,
            Esp_Fel_1="Max: 150 Pa", Esp_Fel_2="Max: 300 Pa", Esp_Fel_3="Max: 450 Pa", Esp_NG="Max: 600 Pa", 
            Esp_Tem="18-25 °C", Esp_Hum="30-65 %HR",
            titulo_uma=self.titulo_patalla,

            page=self.page,
            reloj_global=self.reloj_global,
        )

        # Modificar el botón de registro directamente
        if hasattr(self.uma_instance, 'btn_registro'):
            self.uma_instance.btn_registro.on_click = self.registrar_manual

        # Controles de texto para Manometros
        self.txt_pres_m_24_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_30_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_35_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_36_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_50_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_51_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_52_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_53_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_54_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_55_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_56_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_57_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_58_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_59_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_60_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_61_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_62_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_63_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_64_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_65_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_66_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_67_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_68_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_69_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_70_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)
        self.txt_pres_m_72_09 = ft.Text("-- Pa", size=20, weight=ft.FontWeight.BOLD)

        ################################### CONTENEDOR DE LA PANTALLA  DE UMAS ####################################
        """ Componentes que conforman la seccion de manejadoras """
        self.home_container_1 = ft.Container(
            expand=True,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    border_radius=20,
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    content=ft.Text(self.titulo_patalla,
                                        font_family="Univers",
                                        size=30,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                                self.btn_connect3,
                                ft.Container(
                                    height=35,
                                    width=35,
                                    border_radius=20,
                                    alignment=ft.alignment.center,
                                    content=ft.Icon(
                                        ft.Icons.SETTINGS,
                                        color=ft.Colors.BLUE_GREY_600,
                                        size=30,
                                    ),
                                    tooltip="Configuración",
                                    on_click = lambda e: self.change_page(3)
                                )
                            ]
                        )
                    ),
                    ft.Container(
                        alignment=ft.alignment.bottom_center,
                        height=550,
                        expand=True,
                        content=self.uma_instance,
                    )
                ]
            )
        )

        ################################### CONTENEDOR DE LA PANTALLA DE MANOMETROS ####################################
        """ Componentes que conforman la seccion de los tableros de manometros """
        self.manometros_container_1 = ft.Container(
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Container(
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    border_radius=20,
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    content=ft.Text("TM-SOL",
                                        font_family="Univers",
                                        size=30,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                                self.btn_connect3,
                                ft.Container(
                                    height=35,
                                    width=35,
                                    border_radius=20,
                                    alignment=ft.alignment.center,
                                    content=
                                    ft.Icon(
                                        ft.Icons.SETTINGS,
                                        color=ft.Colors.BLUE_GREY_600,
                                        size=30,
                                    ),
                                    tooltip="Configuración",
                                    on_click = lambda e: self.change_page(3)
                                )
                            ]
                        )
                    ),
                    ft.Container(
                        bgcolor=self.color_main,
                        expand=True,
                        padding=ft.padding.only(top=17, bottom=17),
                        border_radius=10,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            scroll=ft.ScrollMode.HIDDEN,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.START,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    wrap=True,
                                    spacing=30,
                                    controls=[
                                        ContenedorManometro(dato=self.txt_pres_m_24_09, instrumento="M-COM-177", area=" Esclusa paso de materiales (XVII-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_30_09, instrumento="M-COM-182", area=" Esclusa paso de personal (IV-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_35_09, instrumento="M-COM-186", area=" Esclusa del personal al área técnica (XXIII-A) vs Pasillo general de producción ", especificacion="Especificación: > 5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_36_09, instrumento="M-COM-187", area=" Esclusa de personal al área técnica (XXIII-A) vs Área técnica (XXIII) ", especificacion="Especificación: > 5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_50_09, instrumento="M-COM-201", area=" Granulación y recubrimiento (IV) vs Esclusa paso de personal (IV-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_51_09, instrumento="M-COM-202", area=" Esclusa paso de materiales (IV-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_52_09, instrumento="M-COM-203", area=" Granilación y recubrimiento (IV) vs Esclusa paso de materiales (IV-B) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_53_09, instrumento="M-COM-204", area=" Esclusa paso de personal (V-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_54_09, instrumento="M-COM-205", area=" Recubrimiento (V) vs Esclusa paso de personal (V-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_55_09, instrumento="M-COM-206", area=" Recubrimiento (V) vs Esclusa paso de materiales (V-B) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_56_09, instrumento="M-COM-227", area=" Esclusa paso de materiales (V-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_57_09, instrumento="M-COM-228", area=" Esclusa paso de materiales (VI-B) vs Pasillo sóliodos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_58_09, instrumento="M-COM-229", area=" Recubrimiento (VI) vs Esclusa paso de personal (VI-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_59_09, instrumento="M-COM-230", area=" Recubrimiento (VI) vs Esclusa paso de materiales (VI-B) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_60_09, instrumento="M-COM-231", area=" Esclusa paso de personal (VI-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_61_09, instrumento="M-COM-232", area=" Encapsulado (VII) vs Esclusa paso de materiales (VII-B) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_62_09, instrumento="M-COM-233", area=" Encapsulado (VII) vs Esclusa paso de personal (VII-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_63_09, instrumento="M-COM-234", area=" Esclusa paso de materiales (VII-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_64_09, instrumento="M-COM-235", area=" Esclusa paso de personal (VII-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_65_09, instrumento="M-COM-236", area=" Esclusa paso de materiales (VIII-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_66_09, instrumento="M-COM-237", area=" Área libre (VIII) vs Esclusa paso de materiales (VIII-B) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_67_09, instrumento="M-COM-238", area=" Área libre (VIII) vs Esclusa paso de personal (VIII-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_68_09, instrumento="M-COM-239", area=" Esclusa paso de personal (VIII-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_69_09, instrumento="M-COM-240", area=" Esclusa paso de materiales (X-B) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_70_09, instrumento="M-COM-241", area=" Esclusa paso de personal (X-A) vs Pasillo sólidos orales (XVIII) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                        ContenedorManometro(dato=self.txt_pres_m_72_09, instrumento="M-COM-243", area=" Área libre (x) vs Esclusa paso de personal (X-A) ", especificacion="Especificación: < -5 Pa", mostrar_boton=False, on_grafica_click=self.abrir_pagina_grafica),
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )
        
        ################################### CONTENEDOR DE LA PANTALLA DE ALERTAS ####################################
        """ Componentes que conforman la seccion de alertas """
        self.alertas_container_1 = ft.Container(
            expand=True,
        )

        # Solo crear config_container si es Administrador
        if self.rol_actual == "Administrador":
            self.config_container = ContenedorConfiguracion(self.page, self.reloj_global, on_registro_manual=self.registrar_manual, usuario_actual=self.usuario_actual)
        else:
            self.config_container = ft.Container(
                width=600,
                height=300,
                bgcolor=ft.Colors.WHITE,
                border_radius=20,
                alignment=ft.alignment.center,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Icon(ft.Icons.LOCK, size=80, color=ft.Colors.GREY_400),
                        ft.Text(
                            "Acceso Restringido",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "Esta sección solo está disponible\npara administradores",
                            size=16,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        )
                    ]
                )
            )

        ################################### CONTENEDOR DE LA PANTALLA DE CONFIGURANCION ####################################
        """ Componentes que conforman la seccion de configuracion """
        self.configuracion_container_1 = ft.Container(
            expand=True,
            content=ft.Column(
                controls=[
                    ft.Container(
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    border_radius=20,
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    content=ft.Text("CONFIGURACIÓN",
                                        font_family="Univers",
                                        size=30,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                                self.btn_connect3,
                            ]
                        )
                    ),

                    ft.Container(
                        bgcolor=self.color_main,
                        alignment=ft.alignment.center,
                        height=550,
                        border_radius=10,
                        expand=True,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                self.config_container,
                            ]
                        )
                    )
                ]
            )
        )

        ################################### PÁGINA 5 (GRÁFICAS) ####################################
        # Los textos que se actualizarán dinámicamente
        self.titulo_grafica_text = ft.Text(
            value="Gráfica del Manómetro",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLACK
        )
        
        # Este Text mostrará el valor actual en tiempo real
        self.presion_actual_display = ft.Text(
            value="-- Pa",
            size=12,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_700
        )
        
        # Textos dinamicos para la leyenda de límites
        self.leyenda_superior_text = ft.Text(
            value="Límite superior (-- Pa)",
            size=11,
            color=ft.Colors.GREY_600
        )

        self.leyenda_inferior_text = ft.Text(
            value="Límite inferior (-- Pa)",
            size=11,
            color=ft.Colors.GREY_600
        )
        
        # Gráfica
        self.grafica_chart = ft.LineChart(
            expand=True,
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.GREY_300),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=10, color=ft.Colors.GREY_300, width=1
            ),
            left_axis=ft.ChartAxis(
                labels_size=40,
                title=ft.Text("Presión (Pa)", size=12),
            ),
            bottom_axis=ft.ChartAxis(
                labels_size=50,
                title=ft.Text("Fecha y Hora", size=12)
            ),
        )
        
        # Línea de la gráfica principal
        self.linea_grafica = ft.LineChartData(
            color=ft.Colors.BLUE_700,
            stroke_width=2,
            curved=False,  # sin curvas - línea recta
            stroke_cap_round=False,
        )
        
        # Línea de límite superior
        self.linea_limite_superior = ft.LineChartData(
            color="#F8BD28",
            stroke_width=2,
            curved=False,
            stroke_cap_round=False,
            dash_pattern=[10, 5],  # Línea punteada
        )
        
        # Línea de límite inferior
        self.linea_limite_inferior = ft.LineChartData(
            color="#6DF828",            
            stroke_width=2,
            curved=False,
            stroke_cap_round=False,
            dash_pattern=[10, 5],
        )

        self.lista_historial_grafica = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Contador de registros
        self.contador_registros = ft.Text(
            "0 registros",
            size=14,
            color=ft.Colors.GREY_600
        )

        self.grafica_container = ft.Container(
            expand=True,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    # Cabecera
                    ft.Container(
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=ft.Colors.WHITE,
                                    bgcolor=ft.Colors.BLUE_GREY_600,
                                    icon_size=20,
                                    on_click=lambda e: self.change_page(1),
                                    tooltip="Volver a Manómetros"
                                ),
                                ft.Container(
                                    border_radius=20,
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    content=self.titulo_grafica_text,
                                ),
                                self.btn_connect3,
                                ft.Container(
                                    height=35,
                                    width=35,
                                    border_radius=20,
                                    alignment=ft.alignment.center,
                                    content=
                                    ft.Icon(
                                        ft.Icons.SETTINGS,
                                        color=ft.Colors.BLUE_GREY_600,
                                        size=30,
                                    ),
                                    tooltip="Configuración",
                                    on_click = lambda e: self.change_page(3)
                                )
                            ]
                        )
                    ),
                    # Contenido principal
                    ft.Container(
                        alignment=ft.alignment.bottom_center,
                        height=550,
                        expand=True,
                        bgcolor=ft.Colors.TRANSPARENT,
                        content=ft.Row(
                            expand=True,
                            spacing=20,
                            controls=[
                                # Panel izquierdo - Grafica
                                ft.Container(
                                    bgcolor=ft.Colors.TRANSPARENT,
                                    expand=2,  # 2/3 del espacio
                                    # border_radius=10,
                                    content=ft.Column(
                                        expand=True,
                                        spacing=10,
                                        controls=[
                                            # Info adicional
                                            ft.Container(
                                                padding=10,
                                                bgcolor=ft.Colors.BLUE_50,
                                                border_radius=5,
                                                content=ft.Column(
                                                    spacing=8,
                                                    controls=[
                                                        ft.Row(
                                                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                            spacing=10,
                                                            controls=[
                                                                ft.Container(
                                                                    alignment=ft.alignment.center,
                                                                    content=ft.Row(
                                                                        alignment=ft.MainAxisAlignment.CENTER,
                                                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                                        controls=[
                                                                            ft.Text("Presión actual:", size=12, color=ft.Colors.GREY_600),
                                                                            self.presion_actual_display,
                                                                        ]
                                                                    )
                                                                ),
                                                                self.contador_registros,
                                                            ]
                                                        ),
                                                        # Leyenda de límites
                                                        ft.Container(
                                                            margin=ft.margin.only(top=5),
                                                            content=ft.Column(
                                                                spacing=3,
                                                                controls=[
                                                                    ft.Row(
                                                                        spacing=15,
                                                                        controls=[
                                                                            ft.Row([
                                                                                ft.Container(width=15, height=2, 
                                                                                            bgcolor="#F8BD28"),
                                                                                self.leyenda_superior_text,
                                                                            ]),
                                                                            ft.Row([
                                                                                ft.Container(width=15, height=2, 
                                                                                            bgcolor="#6DF828"),
                                                                                self.leyenda_inferior_text,
                                                                            ]),
                                                                            ft.Row([
                                                                                ft.Container(width=8, height=8, 
                                                                                            bgcolor=ft.Colors.BLUE_700, 
                                                                                            border_radius=4),
                                                                                ft.Text("Registro", size=11, color=ft.Colors.GREY_600),
                                                                            ]),
                                                                        ]
                                                                    )
                                                                ]
                                                            )
                                                        )
                                                    ]
                                                )
                                            ),
                                            # ft.Divider(height=1, color=ft.Colors.GREY_300),
                                            # Gráfica
                                            ft.Container(
                                                expand=True,
                                                border=ft.border.all(1, ft.Colors.GREY_300),
                                                border_radius=10,
                                                padding=10,
                                                content=self.grafica_chart
                                            )
                                        ]
                                    )
                                ),
                                # Panel derecho - Historial
                                ft.Container(
                                    bgcolor=self.color_main,
                                    expand=True,
                                    border=ft.border.all(1, ft.Colors.GREY_300),
                                    border_radius=10,
                                    padding=10,
                                    content=ft.Column(
                                        spacing=0,
                                        controls=[
                                            ft.Row(
                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                controls=[
                                                    ft.Text("Historial de Registro", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLACK),
                                                ]
                                            ),
                                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                                            ft.Container(
                                                bgcolor=ft.Colors.BLUE_GREY_600,
                                                border_radius=5,
                                                padding=10,
                                                content=ft.Row(
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                                    spacing=10,
                                                    controls=[
                                                        ft.Container(
                                                            width=60,
                                                            alignment=ft.alignment.center,
                                                            content=ft.Text("Presión", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                                        ),
                                                        ft.Container(
                                                            width=65,
                                                            alignment=ft.alignment.center,
                                                            content=ft.Text("Fecha", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                                        ),
                                                        ft.Container(
                                                            width=65,
                                                            alignment=ft.alignment.center,
                                                            content=ft.Text("Hora", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                                        ),
                                                        ft.Container(
                                                            width=50,
                                                            alignment=ft.alignment.center,
                                                            content=ft.Text("Tipo", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
                                                        )
                                                    ]
                                                )
                                            ),
                                            ft.Container(
                                                expand=True,
                                                bgcolor=ft.Colors.WHITE,
                                                border_radius=5,
                                                padding=5,
                                                shadow=ft.BoxShadow(
                                                    spread_radius=2,
                                                    blur_radius=10,
                                                    color=ft.Colors.GREY_400
                                                ),
                                                content=ft.Column(
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                                    expand=True,
                                                    controls=[
                                                        # Área de historial
                                                        ft.Container(
                                                            expand=True,
                                                            border=ft.border.all(1, ft.Colors.GREY_300),
                                                            border_radius=10,
                                                            padding=5,
                                                            alignment=ft.alignment.top_center,
                                                            content=self.lista_historial_grafica
                                                        )
                                                    ]
                                                )
                                            )
                                        ]
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )

        self.btn_UMA_09 = ft.Container(
           content=ft.Text("UMA 09"),
           width=110,
           height=40,
           bgcolor=ft.Colors.GREY_300,
           border=ft.border.all(3, ft.Colors.GREY_600),
           border_radius=10,
           alignment=ft.alignment.center,
           clip_behavior=ft.ClipBehavior.HARD_EDGE,
           on_hover=self.Check_On_Hover,
           on_click = self.Check_On_Click, data=0,
        )

        self.btn_TM_01 = ft.Container(
           content=ft.Text("TM-SOL"),
           width=110,
           height=40,
           bgcolor=ft.Colors.GREY_300,
           border=ft.border.all(3, ft.Colors.GREY_600),
           border_radius=10,
           alignment=ft.alignment.center,
           clip_behavior=ft.ClipBehavior.HARD_EDGE,
           on_hover=self.Check_On_Hover,
           on_click = self.Check_On_Click, data=1,
        )

        self.btn_extra2 = ft.Container(
           content=ft.Text("Extra 2"),
           width=110,
           height=40,
           bgcolor=ft.Colors.GREY_300,
           border=ft.border.all(3, ft.Colors.GREY_600),
           border_radius=10,
           alignment=ft.alignment.center,
           clip_behavior=ft.ClipBehavior.HARD_EDGE,
           on_hover=self.Check_On_Hover,
           on_click = self.Check_On_Click, data=2,
        )

        self.container_list_1 = [
            self.home_container_1,
            self.manometros_container_1,
            self.alertas_container_1,
            self.configuracion_container_1,
            self.grafica_container 
        ]

        self.container_1 = ft.Container(content=self.container_list_1[0], expand=True)

        self.navigation_container = ft.Container(
            width=125,
            bgcolor=self.color_main,
            border_radius=10,
            alignment=ft.alignment.center,
            padding=ft.padding.only(top=15),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=10,
                controls=[
                    # Logo y nombre
                    ft.Container(
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.Container(
                                    width=50,
                                    height=50,
                                    border_radius=15,
                                    bgcolor=ft.Colors.BLUE_GREY_600,
                                    alignment=ft.alignment.center,
                                    shadow=ft.BoxShadow(
                                        spread_radius=0,
                                        blur_radius=5,
                                        color="rgba(39, 245, 180, 0.15)",
                                    ),
                                    content=ft.Icon(
                                        ft.Icons.MONITOR_HEART,
                                        color=ft.Colors.WHITE,
                                        size=25
                                    )
                                ),
                                ft.Column(
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=2,
                                    controls=[
                                        ft.Text(
                                            "Sistema de",
                                            size=10,
                                            weight=ft.FontWeight.BOLD,
                                            color="#2C3E50"
                                        ),
                                        ft.Text(
                                            "Monitoreo y Registro",
                                            size=10,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_GREY_300
                                        )
                                    ]
                                )
                            ]
                        )
                    ),
                    ft.Divider(height=10, color=ft.Colors.WHITE),
                    ft.Column(
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        controls=[
                            self.btn_UMA_09,
                            self.btn_TM_01,
                        ]
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color=ft.Colors.BLUE_GREY_600,
                        tooltip="Cerrar sesión",
                        on_click=self.cerrar_sesion,
                    )
                ]
            )
        )
        # Frame central
        self.frame_2 = ft.Container(
            col=6.70,
            expand=True,
            content=ft.Column(
                controls=[
                    self.container_1,
                ]
            )
        )

        self.resp_container = ft.Container(
            expand=True,
            content = ft.Row(
                expand=True,
                controls=[
                    self.navigation_container,
                    self.frame_2,
                ]
            )
        )

        # Iniciar actualización de datos desde la base de datos con ciclo
        self.iniciar_actualizacion_desde_db()

    def actualizar_contador_alertas(self):
        """Actualiza el contador de alertas en el badge"""
        try:
            if self.notificacion_badge is None:
                return
                
            total_alertas = self.sistema_alertas.contar_alertas()
            
            # NO mostrar el badge si estamos en la página de Alertas
            if total_alertas > 0 and not self.en_pagina_alertas:
                self.notificacion_badge.visible = True
                self.notificacion_badge.content.value = str(total_alertas) if total_alertas <= 99 else "99+"
                
                # Si hay muchas alertas, hacer el badge más pequeño
                if total_alertas > 9:
                    self.notificacion_badge.width = 24
                    self.notificacion_badge.height = 20
                else:
                    self.notificacion_badge.width = 20
                    self.notificacion_badge.height = 20
            else:
                self.notificacion_badge.visible = False
            
            # Actualizar el badge de forma segura - EVITAR EL ERROR
            try:
                # Verificar si el badge está en la página
                if hasattr(self.notificacion_badge, 'page') and self.notificacion_badge.page is not None:
                    self.notificacion_badge.update()
                # Si no está en la página, no hacer nada (evitar el error)
            except Exception as e:
                # Silenciar específicamente el error "must be added to the page first"
                if "must be added to the page first" not in str(e):
                    print(f"Error actualizando badge: {e}")
                # No imprimir nada para el error específico que queremos evitar
        
        except Exception as e:
            print(f"Error en actualizar_contador_alertas: {e}")

# ========== FUNCIÓN PRINCIPAL ==========
def main(page: ft.Page):
    page.title = "Sistema de Monitoreo"
    page.window.width = 1270
    page.window.height = 630
    page.window.alignment = ft.alignment.top_center
    page.window.min_width = 1270
    page.window.min_height = 630
    page.padding=0
    page.window.resizable = False

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Verificar si pyodbc está disponible
    try:
        import pyodbc
        print("✅ PyODBC está disponible")
    except ImportError:
        print("⚠️ PyODBC no está instalado. El sistema funcionará en modo local.")
        # Mostrar advertencia
        page.add(ft.Container(
            padding=30,
            content=ft.Column(
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.WARNING, size=50, color=ft.Colors.ORANGE),
                    ft.Text(
                        "Advertencia: PyODBC no está instalado",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_800,
                    ),
                    ft.Text(
                        "El sistema funcionará en modo local con datos simulados.\n\n"
                        "Para conectar a SQL Server, instala pyodbc:\n"
                        "pip install pyodbc",
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.ElevatedButton(
                        text="Continuar en modo local",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=lambda e: start_app(page),
                    )
                ]
            )
        ))
        page.update()
        return
    
    # Iniciar aplicación normalmente
    start_app(page)

def start_app(page: ft.Page):
    """Inicia la aplicación"""
    ui = UI(page)

if __name__ == "__main__":
    ft.app(target=main)
