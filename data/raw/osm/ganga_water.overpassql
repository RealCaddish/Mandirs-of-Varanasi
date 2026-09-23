[out:json][timeout:120];
(
  nwr["natural"="water"](25.22,82.95,25.36,83.08);
  nwr["waterway"~"^(river|riverbank)$"](25.22,82.95,25.36,83.08);
);
out geom;
