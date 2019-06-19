Editeur de documents
====================

Il est possible de configurer l'outil afin de pouvoir éditer certain document directement via l'interface "en ligne".

Des outils d'édition, libres et gratuits, sont actuellement configurable afin de les utiliser pour consulter et modifier des documents.
_Note:_ Ces outils sont gérés par des équipes complètement différentes, il se peux que certain de leur comportement ne correspondent pas à vos attentes.

etherpad
--------

Editeur pour document textuel.

Site Web
	https://etherpad.org/

Installation
	Le tutoriel de framasoft explique bien comment l'installer
	https://framacloud.org/fr/cultiver-son-jardin/etherpad.html
	
Configurer
	Editer le fichier "settings.py" contenu dans le répertoire de votre instance.
	Ajouter et adapter la ligne ci-dessous:
	 - url : adresse d'accès d'etherpad
	 - apikey : contenu de la clef de sécurité (fichier APIKEY.txt contenu dans l'installation d'etherpad) 
	 
::
	
	# extra
	ETHERPAD = {'url': 'http://localhost:9001', 'apikey': 'jfks5dsdS65lfGHsdSDQ4fsdDG4lklsdq6Gfs4Gsdfos8fs'}
	
Usage
	Dans le gestionnaire de document, vous avez plusieurs action qui apparait alors
	 - Un bouton "+ Fichier" vous permettant de créer un document txt ou html
	 - Un bouton "Editeur" pour ouvrir l'éditeur etherpad.
	 
.. image:: etherpad.png	  

	
ethercalc
---------

Editeur pour tableau de calcul.

Site Web
	https://ethercalc.net/

Installation
	Sur le site de l'éditeur, une petit explication indique comment l'installer.
	
Configurer
	Editer le fichier "settings.py" contenu dans le répertoire de votre instance.
	Ajouter et adapter la ligne ci-dessous:
	 - url : adresse d'accès d'ethercal
	 
::
	
	# extra
	ETHERCALC = {'url': 'http://localhost:8000'}
	
Usage
	Dans le gestionnaire de document, vous avez plusieurs action qui apparait alors
	 - Un bouton "+ Fichier" vous permettant de créer un document csv, ods ou xmlx
	 - Un bouton "Editeur" pour ouvrir l'éditeur ethercalc.
	 
.. image:: ethercalc.png	  
