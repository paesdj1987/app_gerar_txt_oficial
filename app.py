from dash import Dash
import dash_bootstrap_components as dbc
from layout import create_layout
import callbacks
import dash

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.title = "Gerador de TXT"

# Define o layout da aplicação
app.layout = create_layout(app)

# Inicializa os callbacks
callbacks.init_callbacks(app)

if __name__ == '__main__':
    app.run(debug=False)

