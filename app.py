import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import io
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="📊 Dashboard de Calificaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    .insight-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    .employee-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .top-performer {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border: 2px solid #ffd700;
    }
</style>
""", unsafe_allow_html=True)

def cargar_datos(uploaded_file):
    """Función para cargar y procesar el archivo Excel"""
    try:
        # Leer el archivo Excel
        df = pd.read_excel(uploaded_file, sheet_name='CALIFICACIONES')
        
        st.info(f"📊 Archivo original: {len(df)} filas, {len(df.columns)} columnas")
        st.info(f"🏷️ Columnas detectadas: {list(df.columns)}")
        
        # Limpiar y estructurar los datos
        df.columns = ['CEDULA', 'NOMBRE_COMPLETO', 'CARGO', 'PUNTAJE', 'RESULTADO', 'PERIODO']
        
        # Mostrar datos antes de limpiar
        registros_iniciales = len(df)
        st.info(f"📋 Registros iniciales: {registros_iniciales}")
        
        # Limpiar datos paso a paso
        df_limpio = df.copy()
        
        # Eliminar filas completamente vacías
        df_limpio = df_limpio.dropna(how='all')
        st.info(f"📋 Después de eliminar filas vacías: {len(df_limpio)} registros")
        
        # Eliminar filas sin cédula
        df_limpio = df_limpio.dropna(subset=['CEDULA'])
        st.info(f"📋 Después de filtrar por cédula: {len(df_limpio)} registros")
        
        # Convertir puntaje a numérico
        df_limpio['PUNTAJE'] = pd.to_numeric(df_limpio['PUNTAJE'], errors='coerce')
        
        # Eliminar filas sin puntaje válido
        df_limpio = df_limpio.dropna(subset=['PUNTAJE'])
        st.info(f"📋 Después de filtrar puntajes válidos: {len(df_limpio)} registros")
        
        # Mostrar muestra de datos procesados
        st.success(f"✅ Datos procesados exitosamente: {len(df_limpio)} registros válidos")
        
        with st.expander("👀 Ver muestra de datos procesados"):
            st.dataframe(df_limpio.head(10))
        
        return df_limpio
        
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {str(e)}")
        return None

def calcular_estadisticas(df):
    """Calcular estadísticas generales"""
    return {
        'total_evaluaciones': len(df),
        'total_empleados': df['NOMBRE_COMPLETO'].nunique(),
        'promedio_general': df['PUNTAJE'].mean(),
        'puntaje_maximo': df['PUNTAJE'].max(),
        'puntaje_minimo': df['PUNTAJE'].min(),
        'desviacion_estandar': df['PUNTAJE'].std(),
        'mediana': df['PUNTAJE'].median()
    }

def crear_grafico_distribucion(df):
    """Crear gráfico de distribución de resultados"""
    distribucion = df['RESULTADO'].value_counts()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    fig = px.pie(
        values=distribucion.values,
        names=distribucion.index,
        title="📊 Distribución de Resultados de Evaluación",
        color_discrete_sequence=colors,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        font_size=12,
        showlegend=True,
        height=500
    )
    
    return fig

def crear_grafico_cargos(df):
    """Crear gráfico de promedio por cargo"""
    promedio_cargos = df.groupby('CARGO').agg({
        'PUNTAJE': ['mean', 'count'],
        'NOMBRE_COMPLETO': 'nunique'
    }).round(2)
    
    promedio_cargos.columns = ['PROMEDIO', 'EVALUACIONES', 'EMPLEADOS']
    promedio_cargos = promedio_cargos.reset_index().sort_values('PROMEDIO', ascending=True)
    
    # Colores basados en el rendimiento
    colors = ['#ef4444' if x < 3.5 else '#f59e0b' if x < 4.0 else '#10b981' 
              for x in promedio_cargos['PROMEDIO']]
    
    fig = px.bar(
        promedio_cargos,
        x='PROMEDIO',
        y='CARGO',
        orientation='h',
        title="🏢 Promedio de Calificación por Cargo",
        color='PROMEDIO',
        color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'],
        range_color=[0, 5]
    )
    
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Promedio: %{x:.2f}<br>Evaluaciones: %{customdata[0]}<br>Empleados: %{customdata[1]}<extra></extra>',
        customdata=promedio_cargos[['EVALUACIONES', 'EMPLEADOS']].values
    )
    
    fig.update_layout(
        height=max(400, len(promedio_cargos) * 50),
        xaxis=dict(range=[0, 5])
    )
    
    return fig

def analizar_empleados(df):
    """Análizar rendimiento individual de empleados con media móvil adaptativa"""
    empleados = df.groupby(['CEDULA', 'NOMBRE_COMPLETO', 'CARGO']).agg({
        'PUNTAJE': ['mean', 'count', 'std', 'min', 'max'],
        'PERIODO': lambda x: list(x)
    }).round(2)
    
    empleados.columns = ['PROMEDIO', 'EVALUACIONES', 'DESVIACION', 'MIN', 'MAX', 'PERIODOS']
    empleados = empleados.reset_index()
    
    # Función para calcular tendencia con media móvil adaptativa
    def calcular_tendencia_media_movil(cedula):
        # Obtener datos del empleado ordenados cronológicamente
        emp_data = df[df['CEDULA'] == cedula].copy()
        
        # Ordenar por período cronológico
        orden_periodos = {
            'ENERO-FEBRERO': 1, 'FEBRERO-MARZO': 2, 'MARZO-ABRIL': 3,
            'ABRIL-MAYO': 4, 'MAYO-JUNIO': 5, 'JUNIO-JULIO': 6,
            'JULIO-AGOSTO': 7, 'AGOSTO-SEPTIEMBRE': 8, 'SEPTIEMBRE-OCTUBRE': 9,
            'OCTUBRE-NOVIEMBRE': 10, 'NOVIEMBRE-DICIEMBRE': 11, 'DICIEMBRE-ENERO': 12
        }
        
        emp_data['ORDEN'] = emp_data['PERIODO'].map(orden_periodos)
        emp_data = emp_data.sort_values('ORDEN')
        
        puntajes = emp_data['PUNTAJE'].values
        periodos = emp_data['PERIODO'].values
        n_registros = len(puntajes)
        
        # Si tiene menos de 2 registros, no se puede calcular tendencia
        if n_registros < 2:
            return 'Sin datos suficientes ❓', 0, []
        
        # Calcular media móvil adaptativa según número de registros
        if n_registros == 2:
            # Con 2 registros: usar ambos valores
            ventana = 2
            medias_moviles = []
            for i in range(n_registros - ventana + 1):
                media = np.mean(puntajes[i:i + ventana])
                medias_moviles.append(media)
        
        elif n_registros == 3:
            # Con 3 registros: ventana de 2
            ventana = 2
            medias_moviles = []
            for i in range(n_registros - ventana + 1):
                media = np.mean(puntajes[i:i + ventana])
                medias_moviles.append(media)
        
        elif n_registros == 4:
            # Con 4 registros: ventana de 3
            ventana = 3
            medias_moviles = []
            for i in range(n_registros - ventana + 1):
                media = np.mean(puntajes[i:i + ventana])
                medias_moviles.append(media)
        
        else:  # 5 o más registros
            # Con 5+ registros: ventana de 3
            ventana = 3
            medias_moviles = []
            for i in range(n_registros - ventana + 1):
                media = np.mean(puntajes[i:i + ventana])
                medias_moviles.append(media)
        
        # Calcular la tendencia comparando primera y última media móvil
        if len(medias_moviles) >= 2:
            primera_media = medias_moviles[0]
            ultima_media = medias_moviles[-1]
            cambio = ultima_media - primera_media
            
            # Clasificar tendencia según la magnitud del cambio
            if cambio > 0.3:
                tendencia = f'Mejorando Fuerte 📈📈 (+{cambio:.2f})'
            elif cambio > 0.1:
                tendencia = f'Mejorando 📈 (+{cambio:.2f})'
            elif cambio > 0:
                tendencia = f'Mejorando Leve ↗️ (+{cambio:.2f})'
            elif cambio < -0.3:
                tendencia = f'Declinando Fuerte 📉📉 ({cambio:.2f})'
            elif cambio < -0.1:
                tendencia = f'Declinando 📉 ({cambio:.2f})'
            elif cambio < 0:
                tendencia = f'Declinando Leve ↘️ ({cambio:.2f})'
            else:
                tendencia = f'Estable ➡️ ({cambio:.2f})'
        
        elif len(medias_moviles) == 1:
            # Solo una media móvil (caso especial con 2 registros)
            cambio = puntajes[-1] - puntajes[0]
            if cambio > 0.2:
                tendencia = f'Mejorando 📈 (+{cambio:.2f})'
            elif cambio < -0.2:
                tendencia = f'Declinando 📉 ({cambio:.2f})'
            else:
                tendencia = f'Estable ➡️ ({cambio:.2f})'
        else:
            tendencia = 'Sin tendencia calculable ❓'
            cambio = 0
        
        return tendencia, cambio, medias_moviles
    
    # Aplicar cálculo de tendencia y agregar información detallada
    resultados_tendencia = []
    for _, row in empleados.iterrows():
        cedula = row['CEDULA']
        tendencia, cambio, medias_moviles = calcular_tendencia_media_movil(cedula)
        
        # Obtener datos detallados del empleado
        emp_data = df[df['CEDULA'] == cedula].copy()
        orden_periodos = {
            'ENERO-FEBRERO': 1, 'FEBRERO-MARZO': 2, 'MARZO-ABRIL': 3,
            'ABRIL-MAYO': 4, 'MAYO-JUNIO': 5, 'JUNIO-JULIO': 6,
            'JULIO-AGOSTO': 7, 'AGOSTO-SEPTIEMBRE': 8, 'SEPTIEMBRE-OCTUBRE': 9,
            'OCTUBRE-NOVIEMBRE': 10, 'NOVIEMBRE-DICIEMBRE': 11, 'DICIEMBRE-ENERO': 12
        }
        emp_data['ORDEN'] = emp_data['PERIODO'].map(orden_periodos)
        emp_data = emp_data.sort_values('ORDEN')
        
        resultados_tendencia.append({
            'TENDENCIA': tendencia,
            'CAMBIO_NUMERICO': cambio,
            'MEDIAS_MOVILES': medias_moviles,
            'PUNTAJES_CRONOLOGICOS': list(emp_data['PUNTAJE'].values),
            'PERIODOS_CRONOLOGICOS': list(emp_data['PERIODO'].values),
            'NUM_REGISTROS': len(emp_data)
        })
    
    # Agregar resultados al DataFrame
    for i, resultado in enumerate(resultados_tendencia):
        empleados.loc[i, 'TENDENCIA'] = resultado['TENDENCIA']
        empleados.loc[i, 'CAMBIO_NUMERICO'] = resultado['CAMBIO_NUMERICO']
        empleados.loc[i, 'MEDIAS_MOVILES'] = str(resultado['MEDIAS_MOVILES'])
        empleados.loc[i, 'DETALLE_EVALUACIONES'] = f"{resultado['NUM_REGISTROS']} registros"
    
    # Ordenar por promedio descendente
    empleados = empleados.sort_values('PROMEDIO', ascending=False)
    
    return empleados

def main():
    # Header principal
    st.markdown('<h1 class="main-header">📊 Dashboard de Análisis de Calificaciones</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar para carga de archivo
    st.sidebar.header("📁 Carga de Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Selecciona el archivo Excel",
        type=['xlsx', 'xls'],
        help="Carga tu archivo 'Historico_Calificaciones_Actualizado_con_AbrilMayo.xlsx'"
    )
    
    if uploaded_file is not None:
        # Cargar datos
        with st.spinner('Cargando y procesando datos...'):
            df = cargar_datos(uploaded_file)
        
        if df is not None:
            st.success(f"✅ Archivo cargado exitosamente: {len(df)} registros procesados")
            
            # Filtros en sidebar
            st.sidebar.header("🔍 Filtros")
            
            periodos = ['Todos'] + sorted(df['PERIODO'].unique().tolist())
            periodo_seleccionado = st.sidebar.selectbox("Período", periodos)
            
            cargos = ['Todos'] + sorted(df['CARGO'].unique().tolist())
            cargo_seleccionado = st.sidebar.selectbox("Cargo", cargos)
            
            resultados = ['Todos'] + sorted(df['RESULTADO'].unique().tolist())
            resultado_seleccionado = st.sidebar.selectbox("Resultado", resultados)
            
            # Aplicar filtros
            df_filtrado = df.copy()
            if periodo_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['PERIODO'] == periodo_seleccionado]
            if cargo_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['CARGO'] == cargo_seleccionado]
            if resultado_seleccionado != 'Todos':
                df_filtrado = df_filtrado[df_filtrado['RESULTADO'] == resultado_seleccionado]
            
            # Pestañas principales (eliminamos Tendencias y Heatmap)
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Resumen General", 
                "👥 Análisis por Empleado", 
                "🏢 Análisis por Cargo",
                "📋 Análisis de Resultados"
            ])
            
            with tab1:
                st.header("📊 Resumen General")
                
                # Métricas principales
                stats = calcular_estadisticas(df_filtrado)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric(
                        "Total Evaluaciones",
                        f"{stats['total_evaluaciones']:,}",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "Total Empleados",
                        f"{stats['total_empleados']:,}",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Promedio General",
                        f"{stats['promedio_general']:.2f}",
                        delta=None
                    )
                
                with col4:
                    st.metric(
                        "Puntaje Máximo",
                        f"{stats['puntaje_maximo']:.2f}",
                        delta=None
                    )
                
                with col5:
                    st.metric(
                        "Puntaje Mínimo",
                        f"{stats['puntaje_minimo']:.2f}",
                        delta=None
                    )
                
                # Gráficos principales
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_distribucion = crear_grafico_distribucion(df_filtrado)
                    st.plotly_chart(fig_distribucion, use_container_width=True)
                
                with col2:
                    # Estadísticas adicionales
                    st.subheader("📈 Estadísticas Detalladas")
                    
                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>🎯 Métricas Clave</h4>
                        <ul>
                            <li><strong>Mediana:</strong> {stats['mediana']:.2f}</li>
                            <li><strong>Desviación Estándar:</strong> {stats['desviacion_estandar']:.2f}</li>
                            <li><strong>Rango:</strong> {stats['puntaje_maximo'] - stats['puntaje_minimo']:.2f}</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Distribución por rangos de calificación
                    st.subheader("📊 Distribución por Rangos de Calificación")
                    
                    # Crear categorías de rangos basadas en el puntaje según los criterios especificados
                    def clasificar_puntaje(puntaje):
                        if puntaje >= 4.5:
                            return 'SOBRESALIENTE (4.5-5.0)'
                        elif puntaje >= 3.5:
                            return 'ACEPTABLE (3.5-4.4)'
                        else:
                            return 'NO SATISFACTORIO (0.0-3.4)'
                    
                    # Aplicar clasificación
                    df_filtrado['RANGO_CALIF'] = df_filtrado['PUNTAJE'].apply(clasificar_puntaje)
                    
                    # Contar por rangos
                    rango_counts = df_filtrado['RANGO_CALIF'].value_counts()
                    
                    # Ordenar según el nivel de calificación (de mejor a peor)
                    orden_rangos = [
                        'SOBRESALIENTE (4.5-5.0)',
                        'ACEPTABLE (3.5-4.4)',
                        'NO SATISFACTORIO (0.0-3.4)'
                    ]
                    
                    # Reordenar según el orden definido
                    rango_counts = rango_counts.reindex([r for r in orden_rangos if r in rango_counts.index])
                    
                    st.markdown("**Explicación de la Distribución por Rangos:**")
                    st.markdown("""
                    Esta métrica divide todas las calificaciones en 3 categorías según el puntaje obtenido:
                    - **SOBRESALIENTE (4.5-5.0):** Rendimiento excepcional y destacado
                    - **ACEPTABLE (3.5-4.4):** Rendimiento satisfactorio que cumple estándares
                    - **NO SATISFACTORIO (0.0-3.4):** Rendimiento por debajo del estándar mínimo
                    """)
                    
                    # Mostrar distribución con barras de progreso y colores
                    for rango, count in rango_counts.items():
                        porcentaje = (count / len(df_filtrado)) * 100
                        
                        # Asignar color y emoji según el rango
                        if 'SOBRESALIENTE' in rango:
                            color = '🟢'
                            bar_color = '#10b981'  # Verde
                        elif 'ACEPTABLE' in rango:
                            color = '🟡'
                            bar_color = '#f59e0b'  # Amarillo
                        else:  # NO SATISFACTORIO
                            color = '🔴'
                            bar_color = '#ef4444'  # Rojo
                        
                        # Crear columnas para mejor visualización
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"{color} **{rango}**")
                            st.progress(porcentaje / 100)
                        
                        with col2:
                            st.metric(
                                label="",
                                value=f"{count}",
                                delta=f"{porcentaje:.1f}%"
                            )
            
            with tab2:
                st.header("👥 Análisis por Empleado")
                
                empleados_analisis = analizar_empleados(df_filtrado)
                
                # Top performers
                st.subheader("🏆 Top Performers")
                
                col1, col2, col3 = st.columns(3)
                
                top_3 = empleados_analisis.head(3)
                
                with col1:
                    if len(top_3) > 0:
                        emp = top_3.iloc[0]
                        st.markdown(f"""
                        <div class="top-performer">
                            <h3>🥇 1er Lugar</h3>
                            <strong>{emp['NOMBRE_COMPLETO']}</strong><br>
                            <strong>Cédula: {emp['CEDULA']}</strong><br>
                            <strong>Promedio: {emp['PROMEDIO']:.2f}</strong><br>
                            Cargo: {emp['CARGO']}<br>
                            Tendencia: {emp['TENDENCIA']}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    if len(top_3) > 1:
                        emp = top_3.iloc[1]
                        st.markdown(f"""
                        <div class="top-performer">
                            <h3>🥈 2do Lugar</h3>
                            <strong>{emp['NOMBRE_COMPLETO']}</strong><br>
                            <strong>Cédula: {emp['CEDULA']}</strong><br>
                            <strong>Promedio: {emp['PROMEDIO']:.2f}</strong><br>
                            Cargo: {emp['CARGO']}<br>
                            Tendencia: {emp['TENDENCIA']}
                        </div>
                        """, unsafe_allow_html=True)
                
                with col3:
                    if len(top_3) > 2:
                        emp = top_3.iloc[2]
                        st.markdown(f"""
                        <div class="top-performer">
                            <h3>🥉 3er Lugar</h3>
                            <strong>{emp['NOMBRE_COMPLETO']}</strong><br>
                            <strong>Cédula: {emp['CEDULA']}</strong><br>
                            <strong>Promedio: {emp['PROMEDIO']:.2f}</strong><br>
                            Cargo: {emp['CARGO']}<br>
                            Tendencia: {emp['TENDENCIA']}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Tabla detallada (ACTUALIZADA para mostrar cédula y nombre completo)
                st.subheader("📋 Ranking Completo")
                
                # Preparar datos para mostrar - MANTENER NOMBRE COMPLETO Y AGREGAR CEDULA
                empleados_display = empleados_analisis.copy()
                
                # Mostrar tabla principal con CEDULA y NOMBRE_COMPLETO
                st.dataframe(
                    empleados_display[['CEDULA', 'NOMBRE_COMPLETO', 'CARGO', 'PROMEDIO', 'EVALUACIONES', 'TENDENCIA', 'DETALLE_EVALUACIONES']],
                    use_container_width=True,
                    height=400
                )
                
                # Sección explicativa de la metodología
                with st.expander("📊 ¿Cómo se calcula la tendencia con Media Móvil?"):
                    st.markdown("""
                    ### 📈 Metodología de Cálculo de Tendencias
                    
                    La tendencia se calcula usando **Media Móvil Adaptativa** según el número de registros de cada empleado:
                    
                    #### 🔧 Ventanas de Media Móvil por Número de Registros:
                    - **2 registros:** Ventana de 2 → 1 media móvil
                    - **3 registros:** Ventana de 2 → 2 medias móviles  
                    - **4 registros:** Ventana de 3 → 2 medias móviles
                    - **5+ registros:** Ventana de 3 → 3+ medias móviles
                    
                    #### 📊 Proceso de Cálculo:
                    1. **Ordenar evaluaciones** cronológicamente por período
                    2. **Calcular medias móviles** según la ventana correspondiente
                    3. **Comparar primera vs última** media móvil
                    4. **Clasificar tendencia** según la magnitud del cambio
                    
                    #### 🎯 Clasificación de Tendencias:
                    - **📈📈 Mejorando Fuerte:** +0.3 o más
                    - **📈 Mejorando:** +0.1 a +0.29
                    - **↗️ Mejorando Leve:** +0.01 a +0.09
                    - **➡️ Estable:** -0.00 a +0.00
                    - **↘️ Declinando Leve:** -0.01 a -0.09
                    - **📉 Declinando:** -0.1 a -0.29
                    - **📉📉 Declinando Fuerte:** -0.3 o menos
                    
                    #### 💡 Ventajas de la Media Móvil:
                    - **Reduce ruido:** Suaviza fluctuaciones temporales
                    - **Adaptativa:** Se ajusta al número de datos disponibles
                    - **Robusta:** Menos sensible a valores atípicos
                    - **Cronológica:** Respeta el orden temporal real
                    """)
                
                # Ejemplos interactivos
                with st.expander("🔍 Ver ejemplo detallado de cálculo"):
                    st.markdown("### 📋 Ejemplo con Empleado Real")
                    
                    if len(empleados_analisis) > 0:
                        # Tomar el primer empleado como ejemplo
                        ejemplo_emp = empleados_analisis.iloc[0]
                        cedula_ejemplo = ejemplo_emp['CEDULA']
                        
                        # Obtener datos cronológicos del empleado ejemplo
                        emp_ejemplo = df[df['CEDULA'] == cedula_ejemplo].copy()
                        orden_periodos = {
                            'ENERO-FEBRERO': 1, 'FEBRERO-MARZO': 2, 'MARZO-ABRIL': 3,
                            'ABRIL-MAYO': 4, 'MAYO-JUNIO': 5, 'JUNIO-JULIO': 6
                        }
                        emp_ejemplo['ORDEN'] = emp_ejemplo['PERIODO'].map(orden_periodos)
                        emp_ejemplo = emp_ejemplo.sort_values('ORDEN')
                        
                        st.write(f"**Empleado:** {ejemplo_emp['NOMBRE_COMPLETO']}")
                        st.write(f"**Cédula:** {ejemplo_emp['CEDULA']}")
                        st.write(f"**Número de registros:** {len(emp_ejemplo)}")
                        
                        # Mostrar datos cronológicos
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**📅 Evaluaciones Cronológicas:**")
                            for i, (_, row) in enumerate(emp_ejemplo.iterrows()):
                                st.write(f"{i+1}. {row['PERIODO']}: {row['PUNTAJE']}")
                        
                        with col2:
                            st.write("**📊 Cálculo de Media Móvil:**")
                            puntajes = emp_ejemplo['PUNTAJE'].values
                            n_registros = len(puntajes)
                            
                            if n_registros >= 2:
                                if n_registros == 2:
                                    ventana = 2
                                elif n_registros == 3:
                                    ventana = 2
                                else:
                                    ventana = 3
                                
                                st.write(f"Ventana seleccionada: {ventana}")
                                
                                medias_moviles = []
                                for i in range(n_registros - ventana + 1):
                                    media = np.mean(puntajes[i:i + ventana])
                                    medias_moviles.append(media)
                                    valores_usados = puntajes[i:i + ventana]
                                    st.write(f"Media {i+1}: {valores_usados} → {media:.2f}")
                                
                                if len(medias_moviles) >= 2:
                                    cambio = medias_moviles[-1] - medias_moviles[0]
                                    st.write(f"**Cambio:** {medias_moviles[-1]:.2f} - {medias_moviles[0]:.2f} = {cambio:.2f}")
                                    st.write(f"**Tendencia:** {ejemplo_emp['TENDENCIA']}")
                
                # Botón de descarga ACTUALIZADO
                csv = empleados_display[['CEDULA', 'NOMBRE_COMPLETO', 'CARGO', 'PROMEDIO', 'EVALUACIONES', 'TENDENCIA', 'DETALLE_EVALUACIONES']].to_csv(index=False, encoding='utf-8')
                st.download_button(
                    label="📥 Descargar Análisis Completo (CSV)",
                    data=csv,
                    file_name=f"analisis_empleados_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with tab3:
                st.header("🏢 Análisis por Cargo")
                
                # Gráfico principal
                fig_cargos = crear_grafico_cargos(df_filtrado)
                st.plotly_chart(fig_cargos, use_container_width=True)
                
                # Estadísticas por cargo
                st.subheader("📊 Estadísticas Detalladas por Cargo")
                
                stats_cargos = df_filtrado.groupby('CARGO').agg({
                    'PUNTAJE': ['mean', 'std', 'min', 'max', 'count'],
                    'NOMBRE_COMPLETO': 'nunique'
                }).round(2)
                
                stats_cargos.columns = ['PROMEDIO', 'DESV_EST', 'MIN', 'MAX', 'EVALUACIONES', 'EMPLEADOS']
                stats_cargos = stats_cargos.reset_index().sort_values('PROMEDIO', ascending=False)
                
                st.dataframe(stats_cargos, use_container_width=True)
                
            with tab4:
                st.header("📋 Análisis de Principales Resultados y Recomendaciones")
                
                # Calcular métricas clave para el análisis
                stats = calcular_estadisticas(df_filtrado)
                empleados_analisis = analizar_empleados(df_filtrado)
                
                # Análisis de distribución por rangos
                def clasificar_puntaje_analisis(puntaje):
                    if puntaje >= 4.5:
                        return 'SOBRESALIENTE'
                    elif puntaje >= 3.5:
                        return 'ACEPTABLE'
                    else:
                        return 'NO SATISFACTORIO'
                
                df_filtrado['CATEGORIA'] = df_filtrado['PUNTAJE'].apply(clasificar_puntaje_analisis)
                distribucion_categorias = df_filtrado['CATEGORIA'].value_counts()
                
                # Análisis de tendencias
                empleados_mejorando = empleados_analisis[empleados_analisis['TENDENCIA'].str.contains('Mejorando', na=False)]
                empleados_declinando = empleados_analisis[empleados_analisis['TENDENCIA'].str.contains('Declinando', na=False)]
                empleados_estables = empleados_analisis[empleados_analisis['TENDENCIA'].str.contains('Estable', na=False)]
                
                # Análisis por cargo
                analisis_cargos = df_filtrado.groupby('CARGO').agg({
                    'PUNTAJE': ['mean', 'count', 'std'],
                    'NOMBRE_COMPLETO': 'nunique'
                }).round(2)
                analisis_cargos.columns = ['PROMEDIO', 'EVALUACIONES', 'DESVIACION', 'EMPLEADOS']
                analisis_cargos = analisis_cargos.reset_index().sort_values('PROMEDIO', ascending=False)
                
                # Análisis temporal (si hay múltiples períodos)
                if len(df['PERIODO'].unique()) > 1:
                    analisis_temporal = df.groupby('PERIODO')['PUNTAJE'].agg(['mean', 'count']).reset_index()
                    analisis_temporal.columns = ['PERIODO', 'PROMEDIO', 'EVALUACIONES']
                    # Ordenar cronológicamente
                    orden_periodos = {
                        'ENERO-FEBRERO': 1, 'FEBRERO-MARZO': 2, 'MARZO-ABRIL': 3,
                        'ABRIL-MAYO': 4, 'MAYO-JUNIO': 5, 'JUNIO-JULIO': 6,
                        'JULIO-AGOSTO': 7, 'AGOSTO-SEPTIEMBRE': 8, 'SEPTIEMBRE-OCTUBRE': 9,
                        'OCTUBRE-NOVIEMBRE': 10, 'NOVIEMBRE-DICIEMBRE': 11, 'DICIEMBRE-ENERO': 12
                    }
                    analisis_temporal['ORDEN'] = analisis_temporal['PERIODO'].map(orden_periodos)
                    analisis_temporal = analisis_temporal.sort_values('ORDEN')
                
                # Sección 1: Hallazgos Principales
                st.subheader("🔍 Principales Hallazgos")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 **Rendimiento General**")
                    
                    # Calcular porcentajes
                    total_eval = len(df_filtrado)
                    pct_sobresaliente = (distribucion_categorias.get('SOBRESALIENTE', 0) / total_eval) * 100
                    pct_aceptable = (distribucion_categorias.get('ACEPTABLE', 0) / total_eval) * 100
                    pct_no_satisfactorio = (distribucion_categorias.get('NO SATISFACTORIO', 0) / total_eval) * 100
                    
                    # Determinar estado general
                    if pct_sobresaliente + pct_aceptable >= 85:
                        estado_general = "🟢 **EXCELENTE**"
                        icono_estado = "✅"
                    elif pct_sobresaliente + pct_aceptable >= 70:
                        estado_general = "🟡 **BUENO**"
                        icono_estado = "⚠️"
                    else:
                        estado_general = "🔴 **REQUIERE ATENCIÓN**" 
                        icono_estado = "🚨"
                    
                    st.markdown(f"""
                    **Estado General:** {estado_general}
                    
                    - **Promedio Organizacional:** {stats['promedio_general']:.2f}/5.0
                    - **Evaluaciones Satisfactorias:** {pct_sobresaliente + pct_aceptable:.1f}%
                    - **Nivel Sobresaliente:** {pct_sobresaliente:.1f}%
                    - **Necesitan Mejora:** {pct_no_satisfactorio:.1f}%
                    """)
                    
                    # Análisis de variabilidad
                    if stats['desviacion_estandar'] < 0.5:
                        variabilidad = "🎯 **Baja variabilidad** - Rendimiento homogéneo"
                    elif stats['desviacion_estandar'] < 1.0:
                        variabilidad = "📊 **Variabilidad moderada** - Diferencias normales"
                    else:
                        variabilidad = "📈 **Alta variabilidad** - Diferencias significativas"
                    
                    st.markdown(f"**Variabilidad:** {variabilidad}")
                
                with col2:
                    st.markdown("### 📈 **Tendencias de Desarrollo**")
                    
                    total_empleados = len(empleados_analisis)
                    pct_mejorando = (len(empleados_mejorando) / total_empleados) * 100 if total_empleados > 0 else 0
                    pct_declinando = (len(empleados_declinando) / total_empleados) * 100 if total_empleados > 0 else 0
                    pct_estables = (len(empleados_estables) / total_empleados) * 100 if total_empleados > 0 else 0
                    
                    # Determinar tendencia organizacional
                    if pct_mejorando > pct_declinando:
                        if pct_mejorando > 50:
                            tendencia_org = "📈 **CRECIMIENTO FUERTE**"
                        else:
                            tendencia_org = "↗️ **CRECIMIENTO MODERADO**"
                    elif pct_declinando > pct_mejorando:
                        if pct_declinando > 50:
                            tendencia_org = "📉 **DECLIVE PREOCUPANTE**"
                        else:
                            tendencia_org = "↘️ **DECLIVE MODERADO**"
                    else:
                        tendencia_org = "➡️ **ESTABILIDAD**"
                    
                    st.markdown(f"""
                    **Tendencia Organizacional:** {tendencia_org}
                    
                    - **Empleados Mejorando:** {len(empleados_mejorando)} ({pct_mejorando:.1f}%)
                    - **Empleados Estables:** {len(empleados_estables)} ({pct_estables:.1f}%)
                    - **Empleados Declinando:** {len(empleados_declinando)} ({pct_declinando:.1f}%)
                    """)
                
                # Sección 2: Análisis por Áreas Críticas
                st.markdown("---")
                st.subheader("🎯 Análisis por Áreas Críticas")
                
                # Top 3 y Bottom 3 cargos
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🏆 **Cargos con Mejor Rendimiento**")
                    top_cargos = analisis_cargos.head(3)
                    
                    for i, (_, cargo) in enumerate(top_cargos.iterrows()):
                        emoji = ['🥇', '🥈', '🥉'][i]
                        st.markdown(f"""
                        **{emoji} {cargo['CARGO']}**
                        - Promedio: {cargo['PROMEDIO']:.2f}
                        - Empleados: {cargo['EMPLEADOS']}
                        - Evaluaciones: {cargo['EVALUACIONES']}
                        """)
                
                with col2:
                    st.markdown("### ⚠️ **Cargos que Requieren Atención**")
                    bottom_cargos = analisis_cargos.tail(3)
                    
                    for _, cargo in bottom_cargos.iterrows():
                        color = "🔴" if cargo['PROMEDIO'] < 3.5 else "🟡"
                        st.markdown(f"""
                        **{color} {cargo['CARGO']}**
                        - Promedio: {cargo['PROMEDIO']:.2f}
                        - Empleados: {cargo['EMPLEADOS']}
                        - Evaluaciones: {cargo['EVALUACIONES']}
                        """)
                
                # Sección 3: Evolución Temporal (si aplica)
                if len(df['PERIODO'].unique()) > 1:
                    st.markdown("---")
                    st.subheader("📅 Evolución Temporal")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Mostrar evolución
                        for i, (_, periodo) in enumerate(analisis_temporal.iterrows()):
                            if i == 0:
                                st.markdown(f"**{periodo['PERIODO']}:** {periodo['PROMEDIO']:.2f} (Baseline)")
                            else:
                                periodo_anterior = analisis_temporal.iloc[i-1]
                                cambio = periodo['PROMEDIO'] - periodo_anterior['PROMEDIO']
                                if cambio > 0:
                                    st.markdown(f"**{periodo['PERIODO']}:** {periodo['PROMEDIO']:.2f} (📈 +{cambio:.2f})")
                                elif cambio < 0:
                                    st.markdown(f"**{periodo['PERIODO']}:** {periodo['PROMEDIO']:.2f} (📉 {cambio:.2f})")
                                else:
                                    st.markdown(f"**{periodo['PERIODO']}:** {periodo['PROMEDIO']:.2f} (➡️ Sin cambio)")
                    
                    with col2:
                        # Tendencia temporal general
                        if len(analisis_temporal) >= 2:
                            cambio_total = analisis_temporal.iloc[-1]['PROMEDIO'] - analisis_temporal.iloc[0]['PROMEDIO']
                            if cambio_total > 0.1:
                                st.success(f"📈 Mejora temporal: +{cambio_total:.2f}")
                            elif cambio_total < -0.1:
                                st.error(f"📉 Declive temporal: {cambio_total:.2f}")
                            else:
                                st.info(f"➡️ Estabilidad temporal: {cambio_total:.2f}")
                
                # Sección 4: Recomendaciones Estratégicas
                st.markdown("---")
                st.subheader("💡 Recomendaciones Estratégicas")
                
                # Generar recomendaciones basadas en el análisis
                recomendaciones = []
                
                # Recomendaciones por rendimiento general
                if pct_no_satisfactorio > 20:
                    recomendaciones.append({
                        'prioridad': '🚨 ALTA',
                        'area': 'Rendimiento General',
                        'recomendacion': f'Implementar plan de mejoramiento inmediato. {pct_no_satisfactorio:.1f}% de evaluaciones están por debajo del estándar mínimo.',
                        'acciones': [
                            'Identificar causas raíz del bajo rendimiento',
                            'Diseñar programas de capacitación específicos',
                            'Establecer seguimiento quincenal',
                            'Asignar mentores o supervisores de apoyo'
                        ]
                    })
                
                if pct_sobresaliente < 20:
                    recomendaciones.append({
                        'prioridad': '🟡 MEDIA',
                        'area': 'Desarrollo de Talento',
                        'recomendacion': f'Solo {pct_sobresaliente:.1f}% alcanza nivel sobresaliente (≥4.5). Oportunidad de desarrollar más talento de alto rendimiento.',
                        'acciones': [
                            'Programas de desarrollo de liderazgo',
                            'Reconocimiento y retención de top performers',
                            'Planes de carrera más claros',
                            'Proyectos desafiantes para empleados destacados'
                        ]
                    })
                
                # Recomendaciones por tendencias
                if pct_declinando > 30:
                    recomendaciones.append({
                        'prioridad': '🚨 ALTA',
                        'area': 'Tendencias Negativas',
                        'recomendacion': f'{pct_declinando:.1f}% de empleados muestran declive en rendimiento.',
                        'acciones': [
                            'Investigar factores organizacionales que afectan moral',
                            'Revisar cargas de trabajo y recursos disponibles',
                            'Implementar programas de bienestar laboral',
                            'Evaluación de clima organizacional'
                        ]
                    })
                
                # Recomendaciones por cargos críticos
                cargos_criticos = analisis_cargos[analisis_cargos['PROMEDIO'] < 3.5]
                if len(cargos_criticos) > 0:
                    recomendaciones.append({
                        'prioridad': '🟡 MEDIA',
                        'area': 'Cargos Específicos',
                        'recomendacion': f'Los siguientes cargos requieren atención: {", ".join(cargos_criticos["CARGO"].tolist())}',
                        'acciones': [
                            'Análisis específico de competencias requeridas',
                            'Revisión de procesos de selección y onboarding',
                            'Capacitación técnica especializada',
                            'Redistribución de responsabilidades si es necesario'
                        ]
                    })
                
                # Si no hay problemas críticos, enfocarse en mejora continua
                if len(recomendaciones) == 0 or all(r['prioridad'] == '🟡 MEDIA' for r in recomendaciones):
                    recomendaciones.append({
                        'prioridad': '🟢 MANTENIMIENTO',
                        'area': 'Mejora Continua',
                        'recomendacion': 'El rendimiento general es satisfactorio. Enfocarse en mantener y mejorar gradualmente.',
                        'acciones': [
                            'Mantener programas de desarrollo actuales',
                            'Implementar innovaciones graduales',
                            'Sistemas de reconocimiento regulares',
                            'Benchmarking con mejores prácticas del sector'
                        ]
                    })
                
                # Mostrar recomendaciones
                for i, rec in enumerate(recomendaciones, 1):
                    with st.expander(f"{rec['prioridad']} - {rec['area']}"):
                        st.markdown(f"**Situación:** {rec['recomendacion']}")
                        st.markdown("**Acciones Recomendadas:**")
                        for accion in rec['acciones']:
                            st.markdown(f"• {accion}")
                
                # Sección 5: Métricas de Seguimiento
                st.markdown("---")
                st.subheader("📊 Métricas Clave para Seguimiento")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "🎯 Índice de Calidad",
                        f"{pct_sobresaliente + pct_aceptable:.1f}%",
                        delta=f"Meta: ≥85%",
                        help="Porcentaje de evaluaciones satisfactorias (≥3.5)"
                    )
                
                with col2:
                    st.metric(
                        "⭐ Índice de Excelencia", 
                        f"{pct_sobresaliente:.1f}%",
                        delta=f"Meta: ≥25%",
                        help="Porcentaje de evaluaciones sobresalientes (≥4.5)"
                    )
                
                with col3:
                    st.metric(
                        "📈 Empleados en Crecimiento",
                        f"{len(empleados_mejorando)}",
                        delta=f"{pct_mejorando:.1f}% del total",
                        help="Empleados con tendencia positiva"
                    )
                
                with col4:
                    st.metric(
                        "⚠️ Empleados en Riesgo",
                        f"{len(empleados_declinando)}",
                        delta=f"{pct_declinando:.1f}% del total", 
                        help="Empleados con tendencia negativa"
                    )
                
                # Botón para exportar el análisis
                st.markdown("---")
                
                # Preparar datos para exportar
                resumen_ejecutivo = f"""
                ANÁLISIS DE CALIFICACIONES - RESUMEN EJECUTIVO
                =============================================
                
                RENDIMIENTO GENERAL:
                - Estado: {estado_general.replace('*', '').replace('🟢', '').replace('🟡', '').replace('🔴', '')}
                - Promedio Organizacional: {stats['promedio_general']:.2f}/5.0
                - Evaluaciones Satisfactorias: {pct_sobresaliente + pct_aceptable:.1f}%
                - Nivel Sobresaliente: {pct_sobresaliente:.1f}%
                - Necesitan Mejora: {pct_no_satisfactorio:.1f}%
                
                TENDENCIAS:
                - Empleados Mejorando: {len(empleados_mejorando)} ({pct_mejorando:.1f}%)
                - Empleados Estables: {len(empleados_estables)} ({pct_estables:.1f}%)
                - Empleados Declinando: {len(empleados_declinando)} ({pct_declinando:.1f}%)
                
                RECOMENDACIONES PRINCIPALES:
                {chr(10).join([f"- {rec['area']}: {rec['recomendacion']}" for rec in recomendaciones[:3]])}
                """
                
                st.download_button(
                    label="📄 Descargar Resumen Ejecutivo",
                    data=resumen_ejecutivo,
                    file_name=f"resumen_ejecutivo_calificaciones_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
    
    else:
        # Página de inicio sin archivo
        st.info("👆 Por favor, carga tu archivo Excel en la barra lateral para comenzar el análisis")
        
        # Mostrar información sobre el formato esperado
        st.subheader("📋 Formato de Archivo Esperado")
        
        st.markdown("""
        Tu archivo Excel debe tener las siguientes columnas:
        
        | CEDULA | NOMBRE COMPLETO | CARGO | PUNTAJE | RESULTADO | PERIODO |
        |--------|----------------|--------|---------|-----------|---------|
        | 1234567 | GARCIA LOPEZ JUAN | AUXILIAR | 4.5 | SOBRESALIENTE | ABRIL-MAYO |
        
        **Descripción de columnas:**
        - **CEDULA:** Número de identificación del empleado
        - **NOMBRE COMPLETO:** Nombre completo del empleado
        - **CARGO:** Posición o cargo del empleado
        - **PUNTAJE:** Calificación numérica (0.0 - 5.0)
        - **RESULTADO:** Categoría de resultado (ej: SOBRESALIENTE, ACEPTABLE, DEFICIENTE)
        - **PERIODO:** Período de evaluación (ej: FEBRERO-MARZO, ABRIL-MAYO)
        """)
        
        # Ejemplo de datos
        st.subheader("📊 Vista Previa del Dashboard")
        st.image("https://via.placeholder.com/800x400/3b82f6/ffffff?text=Dashboard+de+Calificaciones", 
                caption="El dashboard mostrará gráficos interactivos una vez que cargues tu archivo")

if __name__ == "__main__":
    main()
                            