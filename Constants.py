# -*- coding: utf-8 *-*

# Round time
ROUND_TIME = 300

# Cost of tech upgrades
TECH_COST = {
	1: 50,
	2: 150,
	3: 400
}

# Chances to destroy fleet for both attacker [0] and defender [1]
DESTROY_CHANCE = {
	'attacker': 0.6,
	'defender': 0.7
}

# Stats template
STATS_TEMPLATE = {
	'techGained': {},
	'techSpent': {},
	'planetsConquered': {},
	'planetsLost': {},
	'systemsConquered': {},
	'systemsLost': {},
	'fleetsDeployed': {},
	'fleetsDestroyed': {},
	'fleetsLost': {},
	'moveCount': {}
}