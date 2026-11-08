-- 1. Steam -> Workspace 10 when launched
hl.window_rule({
	match = { class = "^(steam)$" },
	workspace = "10 silent",
})

hl.window_rule({
	match = { title = "^(Steam)$" },
	workspace = "10 silent",
})

-- 2. Browser -> Workspace 3 when launched
hl.window_rule({
	match = { class = "^(firefox|zen|librewolf|brave-browser|google-chrome|chromium|microsoft-edge)$" },
	workspace = "3",
})

-- 3. Private / Incognito Browser -> Workspace 9 when launched
hl.window_rule({
	match = {
		class = "^(firefox|zen|librewolf)$",
		title = ".*(Private Browsing).*",
	},
	workspace = "9",
})

hl.window_rule({
	match = {
		class = "^(brave-browser)$",
		title = ".*(Private).*",
	},
	workspace = "9",
})

hl.window_rule({
	match = {
		class = "^(google-chrome|chromium)$",
		title = ".*(Incognito).*",
	},
	workspace = "9",
})

hl.window_rule({
	match = {
		class = "^(microsoft-edge)$",
		title = ".*(InPrivate).*",
	},
	workspace = "9",
})
