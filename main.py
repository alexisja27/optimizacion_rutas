import numpy as np
import networkx as nx
import folium
import matplotlib.pyplot as plt
import webbrowser
import os
import tkinter as tk
from tkinter import ttk

# Coordenadas de los puntos de entrega en la V Región
coords = {
    "Valparaíso": (-33.0458, -71.6197),
    "Viña del Mar": (-33.0245, -71.5518),
    "Quilpué": (-33.0478, -71.4425),
    "Villa Alemana": (-33.0422, -71.3732),
    "Quillota": (-32.8770, -71.2484),
    "San Antonio": (-33.5930, -71.6217),
    "Los Andes": (-32.8334, -70.5987),
    "La Calera": (-32.7833, -71.2072),
    "San Felipe": (-32.7548, -70.7253),
    "Putaendo": (-32.6286, -70.7181),
    "Calle Larga": (-32.8519, -70.5992),
    "Concón": (-32.9292, -71.5315),
    "Quintero": (-32.7770, -71.5261),
    "Papudo": (-32.5117, -71.4427),
}

# Matriz de distancias (estimaciones en kilómetros)
distancias = np.array(
    [
        [0, 8, 17, 26, 51, 105, 141, 77, 120, 135, 140, 12, 35, 70],
        [8, 0, 12, 21, 49, 104, 139, 76, 115, 130, 135, 20, 43, 78],
        [17, 12, 0, 10, 41, 95, 131, 68, 108, 123, 127, 25, 48, 83],
        [26, 21, 10, 0, 37, 92, 127, 63, 101, 116, 120, 35, 58, 93],
        [51, 49, 41, 37, 0, 68, 93, 30, 71, 86, 90, 52, 75, 110],
        [105, 104, 95, 92, 68, 0, 123, 98, 138, 153, 157, 117, 140, 175],
        [141, 139, 131, 127, 93, 123, 0, 73, 15, 25, 30, 112, 135, 170],
        [77, 76, 68, 63, 30, 98, 73, 0, 85, 100, 105, 68, 91, 126],
        [120, 115, 108, 101, 71, 138, 15, 85, 0, 10, 15, 123, 146, 181],
        [135, 130, 123, 116, 86, 153, 25, 100, 10, 0, 5, 138, 161, 196],
        [140, 135, 127, 120, 90, 157, 30, 105, 15, 5, 0, 143, 166, 201],
        [12, 20, 25, 35, 52, 117, 112, 68, 123, 138, 143, 0, 33, 68],
        [35, 43, 48, 58, 75, 140, 135, 91, 146, 161, 166, 33, 0, 35],
        [70, 78, 83, 93, 110, 175, 170, 126, 181, 196, 201, 68, 35, 0],
    ]
)

# Nombres de los puntos de entrega
puntos = list(coords.keys())

# Crear un grafo dirigido
G = nx.DiGraph()

# Añadir nodos y aristas
for i in range(len(puntos)):
    for j in range(len(puntos)):
        if i != j and distancias[i, j] != -1:
            G.add_edge(puntos[i], puntos[j], weight=distancias[i][j])


# Función para encontrar la ruta más corta con múltiples paradas
def ruta_mas_corta_multi_punto(grafo, origen, destinos):
    ruta_completa = []
    punto_actual = origen
    while destinos:
        destino_mas_cercano = min(
            destinos,
            key=lambda destino: nx.dijkstra_path_length(
                grafo, punto_actual, destino, weight="weight"
            ),
        )
        ruta_parcial = nx.dijkstra_path(
            grafo, punto_actual, destino_mas_cercano, weight="weight"
        )
        ruta_completa.extend(ruta_parcial[:-1])
        punto_actual = destino_mas_cercano
        destinos.remove(destino_mas_cercano)
    ruta_completa.append(punto_actual)
    return ruta_completa


# Función para estimar tiempo y costos
def estimar_tiempo_y_costos(ruta, velocidad_promedio=50, costo_por_km_usd=0.5):
    distancia_total = sum(
        distancias[puntos.index(ruta[i])][puntos.index(ruta[i + 1])]
        for i in range(len(ruta) - 1)
    )
    tiempo_estimado = distancia_total / velocidad_promedio  # Tiempo en horas
    costo_estimado_usd = distancia_total * costo_por_km_usd  # Costo en dólares
    costo_estimado_clp = costo_estimado_usd * 800  # Convertir a pesos chilenos (CLP)
    return tiempo_estimado, costo_estimado_clp


# Función para crear el mapa y mostrar la ruta
def crear_mapa(origen, ruta, tiempo_estimado, costo_estimado):
    # Crear el mapa centrado en el primer punto de la ruta
    mapa = folium.Map(location=coords[origen], zoom_start=10)

    # Añadir marcadores para los puntos de la ruta
    for punto in ruta:
        folium.Marker(location=coords[punto], popup=punto).add_to(mapa)

    # Dibujar líneas entre los puntos de la ruta
    for i in range(len(ruta) - 1):
        punto1, punto2 = ruta[i], ruta[i + 1]
        folium.PolyLine(locations=[coords[punto1], coords[punto2]], color="red").add_to(
            mapa
        )

    # Añadir información de tiempo y costo
    folium.Marker(
        location=coords[ruta[-1]],
        popup=f"<b>Tiempo estimado:</b> {tiempo_estimado:.2f} horas<br><b>Costo estimado:</b> ${costo_estimado:,.0f} CLP",
        icon=folium.Icon(color="green"),
    ).add_to(mapa)

    # Guardar el mapa en un archivo HTML
    archivo_html = "ruta_optima_v_region.html"
    mapa.save(archivo_html)
    print(f"El mapa de la ruta optimizada se ha guardado como {archivo_html}")

    # Asegurar la apertura del archivo HTML en el navegador
    ruta_absoluta = os.path.abspath(archivo_html)
    webbrowser.open(f"file://{ruta_absoluta}")


# Función para manejar el evento de encontrar la ruta con múltiples paradas
def encontrar_ruta_multi():
    origen = origen_entry.get()
    destinos = [d.strip() for d in destinos_entry.get().split(",")]
    if origen in coords and all(destino in coords for destino in destinos):
        ruta = ruta_mas_corta_multi_punto(G, origen, destinos)
        tiempo_estimado, costo_estimado = estimar_tiempo_y_costos(ruta)
        print(
            f"La ruta más corta desde {origen} pasando por {', '.join(destinos)} es: {ruta}"
        )
        print(
            f"Tiempo estimado: {tiempo_estimado:.2f} horas, Costo estimado: ${costo_estimado:,.0f} CLP"
        )
        crear_mapa(origen, ruta, tiempo_estimado, costo_estimado)
    else:
        print("Por favor, selecciona puntos de origen y destino válidos.")


# Interfaz gráfica con tkinter
ventana = tk.Tk()
ventana.title("Optimización de Rutas de Reparto")

# Entradas para el origen y destinos
tk.Label(ventana, text="Punto de origen:").grid(row=0, column=0)
origen_entry = ttk.Combobox(ventana, values=puntos)
origen_entry.grid(row=0, column=1)

tk.Label(ventana, text="Puntos de destino (separados por comas):").grid(row=1, column=0)
destinos_entry = tk.Entry(ventana)
destinos_entry.grid(row=1, column=1)

# Botón para encontrar la ruta
tk.Button(ventana, text="Encontrar Ruta", command=encontrar_ruta_multi).grid(
    row=2, columnspan=2
)

ventana.mainloop()
