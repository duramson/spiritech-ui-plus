-- UI+ preview: copies of windows UI+ changes, built from the layout files on disk and built again whenever
-- tools/dev.py installs a change. The client reads XML anew each time it loads it, but Lua only at character login,
-- so a changed layout file shows here at once, while a change to Lua code still needs a login. tools/dev.py installs
-- this package for working on UI+ ("dev.py preview"); players never get it.
local Window = ui.require("core.window")
local NcuView = ui.require("ncu.view")
local ScrollBar = ui.require("core.scroll_bar")

local root = ui.load("root.xml")
ui.root(root)

-- The window frame alone (Core's window.xml and window.lua), around a stand-in content.
local function frame_preview()
	return Window.create({
		title = "Preview: frame",
		content = ui.load("frame.xml"),
		width = 200,
		height = 90,
		resizable = false,
	}), 20, 60
end

-- The NCU window (Core's ncu_window.xml and ncu_slot.xml, sized by ncu.view as loaded at login) with empty slots:
-- ncu.view's own layout runs on a stand-in for the view, which fills the grid with as many slots as fit.
local function ncu_preview()
	local view = setmetatable({ mode = "grid", entries = {}, capacity = 12, table = { width = 0 } }, NcuView)
	view.content = ui.shared_layout("ncu_window.xml")
	view.grid = ui.find(view.content, "ncu_grid")
	ui.visible(ui.find(view.content, "ncu_list"), false)
	local slots = 0
	view.populate = function(self)
		while slots < self.capacity do
			ui.add(self.grid, ui.shared_layout("ncu_slot.xml"))
			slots = slots + 1
		end
		while slots > self.capacity do
			ui.destroy(ui.child(self.grid, slots))
			slots = slots - 1
		end
	end
	return Window.create({
		title = "Preview: NCU",
		content = view.content,
		width = 203,
		height = 124,
		layout = function(window, width, height)
			NcuView.layout(view, window, width, height)
		end,
	}), 240, 60
end

-- Scroll bars (scroll.xml): the client's own beside the original client's (core.scroll_bar), then the experiments in
-- scroll-test-1.xml to scroll-test-4.xml. A test file that is missing, or that the client refuses, is left out.
local bars = {}
local function scroll_preview()
	local content = ui.load("scroll.xml")
	bars[#bars + 1] = ScrollBar.attach(ui.find(content, "preview_ao_scroll"), ui.find(content, "preview_ao_holder"),
		{ step = 40 })
	local tests = ui.find(content, "preview_scroll_tests")
	for index = 1, 4 do
		local ok, view = pcall(ui.load, "scroll-test-" .. index .. ".xml")
		if ok and view then
			ui.add(tests, view)
		end
	end
	return Window.create({
		title = "Preview: scroll bar",
		content = content,
		width = 160,
		height = 185,
		resizable = false,
	}), 460, 60
end

local builders = { frame_preview, ncu_preview, scroll_preview }
local shown = {}

local function rebuild()
	for _, bar in ipairs(bars) do
		bar:detach()
	end
	bars = {}
	for _, frame in ipairs(shown) do
		ui.destroy(frame.root)
	end
	shown = {}
	for _, build in ipairs(builders) do
		local ok, frame, x, y = pcall(build)
		if ok then
			ui.add(root, frame.root)
			ui.place(frame.root, x, y)
			ui.visible(frame.root, true)
			shown[#shown + 1] = frame
		end
	end
end

-- generation.xml holds a number tools/dev.py changes with each install; a new number means new files to show.
local function generation()
	local ok, view = pcall(ui.load, "generation.xml")
	if not ok then
		return nil
	end
	local value = ui.minimum_width(view)
	ui.destroy(view)
	return value
end

local seen, checked = generation(), 0
rebuild()
-- (Through core.scroll_bar, which follows its bars from the package's one update observer.)
ScrollBar.on_update(function(now)
	if now - checked < 1000 then
		return
	end
	checked = now
	local current = generation()
	if current ~= seen then
		seen = current
		rebuild()
	end
end)
