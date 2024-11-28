import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, HeatMap, Fullscreen, Draw
from streamlit_folium import folium_static
import plotly.express as px
from datetime import date, timedelta
from UI import *
from add_data import *
import plotly.graph_objects as go
import io

# Configuration de la page
st.set_page_config(page_title="Unilever", page_icon="🌍", layout="wide")
st.header(":bar_chart: Unilever Dashboard")



# Nom du fichier
file_name = 'Unilever_-_all_versions_-_labels_-_2024-11-28-12-22-34.xlsx'

# Charger les feuilles du fichier Excel
df_unilever = pd.read_excel(file_name, sheet_name='Unilever')
df_gpi = pd.read_excel(file_name, sheet_name='GPI')
df_sondage = pd.read_excel(file_name, sheet_name='Sondage')

print("Fichiers chargés avec succès.")



# Sélection des colonnes spécifiques
df_unilever_cols = ["_index", "_submission_time", "Nom et prénom de l'agent", "Nom de l'établissement","Numéro de téléphone", 
                    "Propriètaire", "Type du PDV", "Province", "Commune", "Quartier", 
                    "Adresse du PDV", "Le point de vente est-il nouveau ou ancien?", 
                    "Quels sont vos commentaires généraux ou ceux du vendeur sur le point de vente?",
                    "_Prendre les coordonnées du point de vente_latitude",
                    "_Prendre les coordonnées du point de vente_longitude"]
df_gpi_cols = ["_index", "Selectionner Parmis ces categories"]
df_sondage_cols = ["_index", "Sorte_caracteristic", "Quantite totale de ${Sorte_caracteristic}", "Prix de vente total de ${Sorte_caracteristic}"]

# Extraire seulement les colonnes nécessaires pour réduire la taille des DataFrames
df_unilever = df_unilever[df_unilever_cols]
df_gpi = df_gpi[df_gpi_cols]
df_sondage = df_sondage[df_sondage_cols]

# Fusionner les DataFrames (corriger l'identifiant de fusion si nécessaire)
df_merged = pd.merge(df_unilever, df_gpi, on='_index', how='left')
df_merged = pd.merge(df_merged, df_sondage, on='_index', how='left')

# Filtrage par date
date1 = st.sidebar.date_input("Choose a start date")
date2 = st.sidebar.date_input("Choose an end date")
date1 = pd.to_datetime(date1)
date2 = pd.to_datetime(date2) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
df_filtered = df_merged[(df_merged["_submission_time"] >= date1) & (df_merged["_submission_time"] <= date2)]

# Filtres supplémentaires
st.sidebar.header("Additional filters :")
filters = {
    "Commune": st.sidebar.multiselect("Commune", sorted(df_filtered["Commune"].unique())),
    "Quartier": st.sidebar.multiselect("Quartier", sorted(df_filtered["Quartier"].unique())),
    "Nom et prénom de l'agent": st.sidebar.multiselect("Agent", sorted(df_filtered["Nom et prénom de l'agent"].unique())),
    "Selectionner Parmis ces categories": st.sidebar.multiselect("Categorie produit", sorted(df_filtered["Selectionner Parmis ces categories"].unique())),
    "Sorte_caracteristic": st.sidebar.multiselect("Produit", sorted(df_filtered["Sorte_caracteristic"].astype(str).unique()))  # Conversion en str
}

for col, selection in filters.items():
    if selection:
        df_filtered = df_filtered[df_filtered[col].isin(selection)]

# Bloc analytique
with st.expander("VIEW EXCEL DATASET"):
    showData = st.multiselect('Filter: ', df_filtered.columns, default=df_unilever_cols)
    st.dataframe(df_filtered[showData], use_container_width=True)


# Convertir le DataFrame filtré en un fichier Excel en mémoire
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_filtered.to_excel(writer, index=False)

# Obtenir le contenu du fichier Excel en mémoire
processed_data = output.getvalue()

# Bouton pour télécharger les données filtrées en format Excel avec une clé unique
st.download_button(
    label="📥 Download filtered data in Excel format",
    data=processed_data,
    file_name="données_filtrées.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download_filtered_data"  # Clé unique pour éviter les conflits d'ID
)

# Affichage de la carte
with st.expander("Mapping"):
    if df_filtered['_Prendre les coordonnées du point de vente_latitude'].isnull().all() or \
       df_filtered['_Prendre les coordonnées du point de vente_longitude'].isnull().all():
        st.error("Les coordonnées de localisation sont toutes manquantes.")
    else:
        latitude_mean = df_filtered['_Prendre les coordonnées du point de vente_latitude'].mean()
        longitude_mean = df_filtered['_Prendre les coordonnées du point de vente_longitude'].mean()
        m = folium.Map(location=[latitude_mean, longitude_mean], zoom_start=4)
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in df_filtered.iterrows():
            if pd.notnull(row['_Prendre les coordonnées du point de vente_latitude']) and \
               pd.notnull(row['_Prendre les coordonnées du point de vente_longitude']):
                
                # Vérification de la date d'achat
                date_achat_str = row.get("_submission_time", None)
                popup_color = "gray"  # Couleur par défaut si la date est inconnue
                
                # if date_achat_str:
                #     try:
                #         # Convertir la chaîne en objet datetime
                #         date_achat = datetime.strptime(date_achat_str, "%Y-%m-%d %H:%M:%S")
                #         today = datetime.now()
                #         difference = today - date_achat

                #         # Vérifier si la date d'achat est dans le dernier mois ou plus
                #         if difference.days <= 30:  # Achat dans le dernier mois
                #             popup_color = "green"
                #         else:  # Plus d'un mois
                #             popup_color = "red"
                #     except ValueError:
                #         # Gérer les dates mal formatées
                #         st.warning(f"Date incorrecte pour le PDV : {row['Nom de l'établissement']}")
                # else:
                #     st.warning("Aucune date d'achat fournie.")



                # Lien Google Maps
                google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin=YOUR_LATITUDE,YOUR_LONGITUDE&destination={row['_Prendre les coordonnées du point de vente_latitude']},{row['_Prendre les coordonnées du point de vente_longitude']}&travelmode=driving"

                popup_content = f"""
                    <h3>Informations sur {row["Nom de l'établissement"]}</h3>
                    <div style='color:{popup_color}; font-size:14px;'>
                        <b>Nom de l'agent :</b> {row["Nom et prénom de l'agent"]}<br>
                        <b>Nom et prénom du proprietaire? :</b> {row["Propriètaire"]}<br>
                        <b>Type du PDV :</b> {row['Type du PDV']}<br>
                        <b>Commune :</b> {row['Commune']}<br>
                        <b>Quartier :</b> {row['Quartier']}<br>
                        <b>Adresse :</b> {row["Adresse du PDV"]}<br>
                        <b>Produit :</b> {row["Sorte_caracteristic"]}<br>
                        <b>Quantite :</b> {row["Quantite totale de ${Sorte_caracteristic}"]}<br>
                        <b>Prix :</b> {row["Prix de vente total de ${Sorte_caracteristic}"]}<br>
                        <b>Numéro de téléphone :</b> {row["Numéro de téléphone"]}<br>
                        <b>Date d'enregistrement :</b> {row['_submission_time']}<br>
                        <b>Voir sur la carte :</b> <a href="{google_maps_url}" target="_blank">Cliquer ici pour obtenir l'itinéraire vers ce point de vente</a>
                    </div>
                """

                # Choisir une icône selon le statut
                icon_color = "green" if popup_color == "green" else "red"

                folium.Marker(
                    location=[row['_Prendre les coordonnées du point de vente_latitude'], 
                              row['_Prendre les coordonnées du point de vente_longitude']],
                    tooltip=row["Nom de l'établissement"],
                    icon=folium.Icon(color=icon_color, icon='fa-dollar-sign', prefix='fa')
                ).add_to(marker_cluster).add_child(folium.Popup(popup_content, max_width=600))

        # Ajout de la heatmap
        heat_data = [[row['_Prendre les coordonnées du point de vente_latitude'], 
                      row['_Prendre les coordonnées du point de vente_longitude']] 
                     for _, row in df_filtered.iterrows()
                     if pd.notnull(row['_Prendre les coordonnées du point de vente_latitude']) and 
                        pd.notnull(row['_Prendre les coordonnées du point de vente_longitude'])]
        if heat_data:
            HeatMap(heat_data).add_to(m)
        Fullscreen(position='topright').add_to(m)
        Draw(export=True).add_to(m)

        # Affichage de la carte
        folium_static(m)


# Load dataset and filters
def UI():
    st.markdown("""<h3 style="color:#002B50;">⚛  BUSINESS ANALYTICS DASHBOARD</h3>""", unsafe_allow_html=True)

if df_filtered is not None and not df_filtered.empty:
    with st.expander("VIEW EXCEL DATASET"):
        showData = st.multiselect('Filter: ', df_filtered.columns, default=df_unilever_cols)
        st.dataframe(df_filtered[showData], use_container_width=True)


# Filtrage et affichage des données
with st.expander("Filter Excel Dataset"):
    filtered_df = dataframe_explorer(df_filtered, case=False)
    st.dataframe(filtered_df, use_container_width=True)

# Convertir le DataFrame filtré en un fichier Excel en mémoire
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    filtered_df.to_excel(writer, index=False)
processed_data = output.getvalue()

# Bouton pour télécharger les données filtrées en format Excel
st.download_button(
    label="📥 Download filtered data in Excel format",
    data=processed_data,
    file_name="données_filtrées.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Supposons que 'filtered_df' est déjà défini dans votre code.

# Graphiques
col1, col2 = st.columns(2)

# Graphe à barres
with col1:
    total_sales = filtered_df['Prix de vente total de ${Sorte_caracteristic}'].sum()  # Total des ventes
    fig2 = go.Figure(
        data=[go.Bar(x=filtered_df['Sorte_caracteristic'].astype(str),  
                      y=filtered_df['Prix de vente total de ${Sorte_caracteristic}'].astype(float))],
        layout=go.Layout(
            title=go.layout.Title(text="Sales by Product Type"),
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            xaxis=dict(showgrid=True, gridcolor='#cecdcd'),
            yaxis=dict(showgrid=True, gridcolor='#cecdcd'),
            font=dict(color='#cecdcd'),
        )
    )
    # Ajouter le total des ventes sur le graphique
    fig2.add_annotation(
        xref='paper', yref='paper',
        x=0.5, y=1.1,
        text=f"Total: ${total_sales:,.2f}",
        showarrow=False,
        font=dict(size=14, color='black'),
        bgcolor='rgba(255, 255, 255, 0.7)',
        bordercolor='black',
        borderwidth=1,
        borderpad=4,
    )
    st.plotly_chart(fig2, use_container_width=True)

# Graphe à secteurs (pie chart)
with col2:
    total_sales_pie = filtered_df['Prix de vente total de ${Sorte_caracteristic}'].sum()  # Total pour le pie chart
    fig = px.pie(filtered_df, values='Prix de vente total de ${Sorte_caracteristic}', 
                  names="Nom et prénom de l'agent", title='Total price per agent (%)')
    fig.update_traces(hole=0.4)
    fig.update_layout(width=800)
    
    # Ajouter le total sur le pie chart
    fig.add_annotation(
        xref='paper', yref='paper',
        x=0.5, y=0.5,
        text=f"Total: ${total_sales_pie:,.2f}",
        showarrow=False,
        font=dict(size=14, color='black'),
        bgcolor='rgba(255, 255, 255, 0.7)',
        bordercolor='black',
        borderwidth=1,
        borderpad=4,
    )
    st.plotly_chart(fig, use_container_width=True)

# Gestion des erreurs
try:
    pass  # Vous pouvez ajouter votre logique ici si nécessaire
except Exception as e:
    st.error(f"Unable to display null, select at least one business location: {e}")


# Chargement des données filtrées depuis le DataFrame `filtered_df`
# Pour cet exemple, on supposera que `filtered_df` est déjà chargé
# filtered_df = ... (votre filtre appliqué à un DataFrame)

# Exemple d'affichage des graphiques
if not filtered_df.empty:
    # Affichage d'un tableau des données filtrées
    st.write("### Overview of filtered data")
    st.dataframe(filtered_df)

    # Graphiques en colonnes
    col1, col2 = st.columns(2)

    # Graphique en camembert : Répartition des ventes par type de produit avec chiffres
    with col1:
        st.write("### Breakdown of Sales by Product Type")
        fig_pie_product = px.pie(
            filtered_df, 
            values='Prix de vente total de ${Sorte_caracteristic}', 
            names='Sorte_caracteristic', 
        )
        fig_pie_product.update_traces(
            textinfo='label+value',  # Affiche le nom du produit et le chiffre total
            textfont_size=15
        )
        st.plotly_chart(fig_pie_product, use_container_width=True)

    # Graphique en camembert : Répartition des ventes par agent avec chiffres
    with col2:
        st.write("### Breakdown of Sales by Agent")
        fig_pie_agent = px.pie(
            filtered_df, 
            values='Prix de vente total de ${Sorte_caracteristic}', 
            names='Nom et prénom de l\'agent', 

        )
        fig_pie_agent.update_traces(
            textinfo='label+value',  # Affiche le nom de l'agent et le chiffre total
            textfont_size=15
        )
        st.plotly_chart(fig_pie_agent, use_container_width=True)

    # Gestion des erreurs
    try:
        pass  # Vous pouvez ajouter votre logique ici si nécessaire
    except Exception as e:
        st.error(f"Unable to display null, select at least one business location: {e}")


    