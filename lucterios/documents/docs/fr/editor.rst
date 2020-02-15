Editeur de documents
====================

Il est possible de configurer l'outil afin de pouvoir éditer certains documents directement via l'interface "en ligne".

Des outils d'édition, libres et gratuits, sont actuellement configurables afin de les utiliser pour consulter et modifier des documents.

**Note :** Ces outils sont gérés par des équipes complètement différentes, il se peut que certains de leurs comportements ne correspondent pas à vos attentes.

Etherpad
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
	 - url : adresse d'accès d'Etherpad
	 - apikey : contenu de la clef de sécurité (fichier APIKEY.txt contenu dans l'installation d'etherpad) 
	 
::
	
	# extra
	ETHERPAD = {'url': 'http://localhost:9001', 'apikey': 'jfks5dsdS65lfGHsdSDQ4fsdDG4lklsdq6Gfs4Gsdfos8fs'}
	
Usage
	Dans le gestionnaire de documents, vous avez plusieurs actions qui apparaissent alors
	 - Un bouton "+ Fichier" vous permettant de créer un document txt ou html
	 - Un bouton "Editeur" pour ouvrir l'éditeur Etherpad.
	 
.. image:: etherpad.png	  

	
Ethercalc
---------

Editeur pour tableau de calcul.

Site Web
	https://ethercalc.net/

Installation
	Sur le site de l'éditeur, une petit explication indique comment l'installer.
	
Configurer
	Editer le fichier "settings.py" contenu dans le répertoire de votre instance.
	Ajouter et adapter la ligne ci-dessous:
	 - url : adresse d'accès d'Ethercal
	 
::
	
	# extra
	ETHERCALC = {'url': 'http://localhost:8000'}
	
Usage
	Dans le gestionnaire de documents, vous avez plusieurs actions qui apparaissent alors
	 - Un bouton "+ Fichier" vous permettant de créer un document csv, ods ou xmlx
	 - Un bouton "Editeur" pour ouvrir l'éditeur Ethercalc.
	 
.. image:: ethercalc.png	  
