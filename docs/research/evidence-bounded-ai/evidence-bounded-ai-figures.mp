% SPDX-License-Identifier: CC-BY-SA-4.0
% State slice: evidence-bounded-aligned-ai-research-paper-v1
% Figure source using the pinned external fiziko MetaPost library.

color fizikoInk, fizikoSepia, fizikoBlue, fizikoGreen, fizikoRust;
color fizikoBlueWash, fizikoGreenWash, fizikoRustWash, fizikoPaper;

fizikoInk := (0.14, 0.12, 0.10);
fizikoSepia := (0.48, 0.30, 0.16);
fizikoBlue := (0.24, 0.36, 0.43);
fizikoGreen := (0.32, 0.42, 0.36);
fizikoRust := (0.55, 0.25, 0.17);
fizikoBlueWash := (0.88, 0.91, 0.92);
fizikoGreenWash := (0.89, 0.92, 0.87);
fizikoRustWash := (0.94, 0.87, 0.83);
fizikoPaper := (0.957, 0.922, 0.843);

minStrokeWidth := 1/2pt;
lightDirection := (-1/8pi, 1/8pi);

def fizikoPanel(expr center, width, height, fillColor, lineColor) =
  save p;
  path p;
  p := unitsquare xscaled width yscaled height
       shifted center shifted (-width/2, -height/2);
  fill p withcolor fillColor;
  draw p withcolor lineColor withpen pencircle scaled 0.8pt;
enddef;

def fizikoMarker(expr center, radius, markerColor) =
  draw sphere.c(2radius) shifted center withcolor markerColor;
enddef;

def fizikoArrow(expr p) =
  drawarrow p withcolor fizikoSepia withpen pencircle scaled 0.85pt;
enddef;

def fizikoRule(expr p) =
  draw p withcolor fizikoSepia withpen pencircle scaled 0.45pt;
enddef;
