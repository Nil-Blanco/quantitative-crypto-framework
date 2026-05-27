import pandas as pd
from binance.client import Client


client = Client()

def descargar_historial(simbolo, intervalo, tiempo_inicio):
    print(f"Descargando historial de {simbolo}...")
    
    
    velas = client.get_historical_klines(simbolo, intervalo, tiempo_inicio)
    
    
    datos = []
    for vela in velas:
        
        tiempo = pd.to_datetime(vela[0], unit='ms') 
        precio_cierre = float(vela[4]) 
        
        datos.append({'Fecha': tiempo, simbolo: precio_cierre})
        
    
    df = pd.DataFrame(datos)
    df.set_index('Fecha', inplace=True)
    return df


intervalo = Client.KLINE_INTERVAL_1HOUR 
tiempo_inicio = "2000 days ago UTC"


df_btc = descargar_historial("BTCUSDT", intervalo, tiempo_inicio)
df_sol = descargar_historial("SOLUSDT", intervalo, tiempo_inicio)
df_eth = descargar_historial("ETHUSDT", intervalo, tiempo_inicio)  
df_paxg = descargar_historial("PAXGUSDT", intervalo, tiempo_inicio) 
df_usdc = descargar_historial("USDCUSDT", intervalo, tiempo_inicio) 



historial_portfolio = df_btc.join([df_sol, df_eth, df_paxg, df_usdc], how='inner')

print("\nDatos listos para el simulador:")
print(historial_portfolio.head())


capital_inicial = 10000.0  
pesos_objetivo = {
    'BTCUSDT': 0.30,  
    'SOLUSDT': 0.10,  
    'ETHUSDT': 0.10,
    'PAXGUSDT': 0.25,  
    'USDCUSDT': 0.25
}
umbral = 0.10 


cantidades = {'BTCUSDT': 0.0, 'SOLUSDT': 0.0, 'ETHUSDT': 0.0, 'PAXGUSDT': 0.0, 'USDCUSDT': 0.0 }




primera_fila = historial_portfolio.iloc[0]
cantidades_iniciales_bh = {}
for activo, peso in pesos_objetivo.items():
    dinero_a_invertir = capital_inicial * peso
    precio_actual = primera_fila[activo]
    cantidades[activo] = dinero_a_invertir / precio_actual
    cantidades_iniciales_bh[activo] = cantidades[activo]

print("\n--- INICIANDO SIMULACIÓN ---")
operaciones = 0
capital_historico = []


for fecha, precios in historial_portfolio.iterrows():
    
   
    valor_total_actual = sum(cantidades[activo] * precios[activo] for activo in pesos_objetivo)
    capital_historico.append(valor_total_actual)
    
    
    for activo, peso_obj in pesos_objetivo.items():
        valor_activo = cantidades[activo] * precios[activo]
        peso_actual = valor_activo / valor_total_actual
        
        
        if abs(peso_actual - peso_obj) > umbral:

            print(f"[{fecha}] Acción en {activo}: Peso estaba al {peso_actual*100:.2f}%. Ajustando al {peso_obj*100:.0f}%")
            
            valor_ideal = valor_total_actual * peso_obj
            
            
            cantidades[activo] = valor_ideal / precios[activo]
            operaciones += 1


capital_final = capital_historico[-1]
rendimiento = ((capital_final - capital_inicial) / capital_inicial) * 100


ultima_fila = historial_portfolio.iloc[-1]
capital_final_bh = sum(cantidades_iniciales_bh[activo] * ultima_fila[activo] for activo in pesos_objetivo)
rendimiento_bh = ((capital_final_bh - capital_inicial) / capital_inicial) * 100

print(f"Capital Inicial: ${capital_inicial:.2f}")
print(f"Capital Final (Bot): ${capital_final:.2f}")
print(f"Rendimiento del Bot: {rendimiento:.2f}%")
print(f"Total de operaciones realizadas: {operaciones}")
print("-----------------------------------")
print(f"Capital Final (Buy & Hold): ${capital_final_bh:.2f}")
print(f"Rendimiento Buy & Hold: {rendimiento_bh:.2f}%")