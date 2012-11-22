# -*- coding: utf-8 *-*

# Round time
ROUND_TIME = 60

# Cost of tech upgrades
TECH_COST = {
	1: 50,
	2: 150,
	3: 400
}

# How much more tech points to give for conquerring planet for the first time?
TECH_POINTS_PLANET_MULTIPLIER = 3

# How much more tech points to give for a planetary system each round?
TECH_POINTS_SYSTEM_MULTIPLIER = 0.2

# Upgrade bonus
UPGRADE_BONUS = {
	'offensive': 0.05,
	'defensive': 0.05,
	'economic': 0.05
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
	'systemsLost': {},
	'fleetsDeployed': {},
	'fleetsDestroyed': {},
	'fleetsLost': {},
	'moveCount': {}
}