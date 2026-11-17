# 15 WEB SERVER DEVICE (cairn/devices/web_server/)
- 15.1 PURPOSE: The one web surface: shows the running system.
- 15.2 WHY: Cairn has a user; the operator, and the librarian's chat, need a web
  face.
- 15.3 INTENTION:
  - 15.3.1 One web server. A device gets a PANE in it, never a server of its own.
  - 15.3.2 The devices across the top (from the rack); the selected device's panes
    below: status, controls, chat, feed (2.3.8). The bus has no page of its
    own: its feed is a sub-panel off the Cairn device's page (5.5.3.7).
  - 15.3.3 A presentation surface: it may collapse an error into a shape, but never
    hides that there was one (Law 7).
  - 15.3.4 It asks devices for what to draw over the bus (get/show).
  - 15.3.5 It runs on one box, so a box that joins the instance starts no web server
    of its own; its devices show in the one server through the buses
    (5.5.3.8).
- 15.4 TOOLS: bus_client, base, public_feed; machine learning_block.
