Light Draw
==========


Light Draw (Modal, Gizmo, Tool operator?)
-------------------

Once clicked in object mode, a modal begins.
You can navigate around the scene as normal.

Phase 1:

``LMB`` selects the face under your cursor, highlights them in green for highlights.
``MMB`` removes selected faces from your selection.
If the users presses ``Esc``, the modal is exited without changes.
If the user presses ``Enter``, the modal finishes by adding a light in a position and angle based on the surfaces selected.

.. code-block:: python
    # for highlights only
    n = averaged or median normal of selected faces
    flattened_hull = faces flattened on axis of averaged normal
    flattened_convex_hull =  convex hull of flattened_hull
    min_dist = greatest diameter of flattened_convex_hull
    Add new light
    Rotate it towards -n

    if lamp type != 'SUN':
        position object at bounding box center, min_dist away from flattened_hull

    # for highlights and shadows, non-sun
    light_surface = extruded surface from selected highlights
    shadow_surface = extruded surface from selected shadows
    subtract shadow_surface from light_surface

    subtract original faces from light_surface

    if no surface remaining:
        return error saying it's impossible

    # light_surface is now bounding surface for light position

    Add new light

Phase 2:

G to grab for lamp, but it snaps to light_surface.
It will point towards highlighted faces.

Parameters:

- Lamp type (post-op) - enum: point, sun(?), area, spot lamp
- Selection ray distance (during drawing) - determines how far to raycast into the scene for mesh selection.
- Extrude distance (during drawing)
- Backface culling (during drawing) - hides green faces that aren't facing the viewport camera.
- Coplanar selection (during drawing) - instead of selecting only the face underneath the cursor, all contiguous coplanar faces are also selected as one large plane.

Phase 2:

With highlighted faces still selected,
user can rotate light, with the pivot point at the center of selected faces.

Light Falloff (Gizmo)
----------------------

Using a scale widget and pivot point,
a user can scale the falloff of a lamp by changing the distance of a light to an object
while inversely scaling the emission value of the light.

Only works on non-sun-type lamps.

Parameters:

- Pivot point: custom cursor

Sun light Scale (Gizmo)
-------------------

Using a scale widget,
a user can scale the emission value of the light.

F stop values?

Only works on sun-type lamps.