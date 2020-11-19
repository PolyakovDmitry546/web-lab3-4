from flask import Flask

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.debug = True

from . import db
db.init_app(app)

from . import auth
app.register_blueprint(auth.bp)

from . import routes
app.register_blueprint(routes.bp)
app.add_url_rule('/', endpoint='index')