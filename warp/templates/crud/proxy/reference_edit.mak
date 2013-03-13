<%page args="fieldName, nameObjs, selectedID, allowNone" />

<select name="warpform-${fieldName}">
  % if allowNone:
      <option value=""${' selected="selected"' if selectedID is None else ""}>
        [None]
      </option>
  % endif
  % for name, obj in nameObjs:
      <option value="${obj.id}"${' selected="selected"' if obj.id == selectedID else ""}>
        ${name}
      </option>
  % endfor
</select>
