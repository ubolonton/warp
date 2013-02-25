<%page args="fieldName, objs, selectedID" />

<select name="warpform-${fieldName}">
  % for obj in objs:
      <option value="${obj.id}"${' selected="selected"' if obj.id == selectedID else ""}>
        ${obj.name}
      </option>
  % endfor
</select>
