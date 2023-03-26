# Light Painter

## Painting

The painting is done using Blender's
[annotation tools](https://docs.blender.org/manual/en/latest/interface/annotate_tool.html)
in the 3D view.
You can find these in the toolshelf on the left-hand side of the 3D view.
These tools are also provided as a pie menu
(default shortcut is `Ctrl + Shift + P` in the 3D view)
and in the Light Painter panel for convenience.

The stroke placement setting is preferred to be "Surface" instead of the default 3D cursor.
You can find this also in the Light Painter panel as well
as in the tool settings of the 3D view header.

Now just paint where you want the light to hit your objects' surfaces!

### What's the best way to paint?

You do not need to fill _every_ surface with the annotation tool.
Draw some simple strokes over surfaces that you would like highlighted by your light.
Keep in mind that the surface's normal you are annotating
will also influence where the light will be finally positioned.

The tool also works best
when your annotation matches the shape of the type of lamp that you want.

- Spot lamps prefer circular shapes.
  But if you do not trust your drawing ability,
  a line or two representing the elliptical width and height is sufficient.
- For area lamps, rectangles, squares, circles or a single line work best.
- Point lamps are the most forgiving since a point lamp's rotation is irrelevant.

## Painting lights

You can find the light operators as a pie menu
(default shortcut is `Shift + P` in the 3D view)
or in the Light Painter panel.

There are several light types:

- point lamp
- sun lamp
- spot lamp
- area lamp
- world sky texture

Also included are these (but since they use emissive materials,
they will not work in Eevee):

- emissive mesh object as a convex hull
- emissive tube - each annotation stroke becomes a "tube" of light -
  great for neon lighting or custom-shaped lighting.

You can press `F9` or click the collapsed panel in the bottom-left corner of the 3D view
to tweak parameters such as light distance, power and color.

### Sun lamp and Sky texture operators

These two have some unique settings, so I will go over that.
There are two options to determine direction: "average" -
which just takes the mean normal of the annotations -
and "occlusion". The latter imitates a sun above the horizon.
For the number of samples given, the operator will iterate over different sun positions
and check how much of your annotation's surface will be hit.
After iterating over all the samples, the operator will choose the best position.

However, this scoring of the best position may result in noonday lighting from above.
To give the artist more control, there is a "Max Sun Elevation" parameter
where you can specify the max elevation of the sun.
This can force the operator to only sample the sun at lower elevations,
giving more dynamic lighting.





