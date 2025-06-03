-- This unit tests validate that each visible technology can be researched.
-- This means that all their prerequisites are visible and researchable.
local unit_test_functions = require("unit-test-functions")

local tech_unlocked_by_script = {
  -- ["tech-name"] = true
}

local tech_hidden = function(tech_prototype)
  return tech_prototype.hidden or not (tech_prototype.enabled or tech_prototype.visible_when_disabled)
end

local suitable_research_lab = function(tech_prototype)
  if not tech_prototype then
    return true
  end -- edge case behaviour

  local has_suitable_lab_inputs = function(entity_prototype)
    if not entity_prototype then
      return
    end -- edge case behaviour
    if not entity_prototype.lab_inputs then
      return #tech_prototype.research_unit_ingredients == 0
    end

    for _, lab_input_item_data in pairs(tech_prototype.research_unit_ingredients) do
      local entity_has_ingredient = false
      for _, research_item_name in pairs(entity_prototype.lab_inputs) do
        entity_has_ingredient = entity_has_ingredient or (lab_input_item_data.name == research_item_name)
      end
      if not entity_has_ingredient then
        return false
      end
    end

    return true
  end

  local entity_filters = {}
  table.insert(entity_filters, { filter = "hidden", invert = true, mode = "and" })
  table.insert(entity_filters, { filter = "type", type = "lab", mode = "and" })
  local entity_prototypes = prototypes.get_entity_filtered(entity_filters)

  for _, entity_prototype in pairs(entity_prototypes) do
    if has_suitable_lab_inputs(entity_prototype) then
      return true
    end
  end
  return false
end

-- TODO accept argument of techs unlocked by script?
local test_technologies_can_be_researched = function()
  local unit_test_result = unit_test_functions.test_successful

  local tech_prototypes = prototypes.technology
  for tech_name, tech_prototype in pairs(tech_prototypes) do
    if (not tech_hidden(tech_prototype)) and not tech_unlocked_by_script[tech_name] then
      -- tech visible and must be researched

      -- STEP 1: verify all prerequisites can be researched
      for prereq_name, prereq_prototype in pairs(tech_prototype.prerequisites) do
        if tech_hidden(prereq_prototype) and not tech_unlocked_by_script[prereq_name] then -- tech cannot be researched
          unit_test_functions.print_msg(
            string.format("Technology %q depends on %q, which is hidden.", tech_name, prereq_name)
          )
          unit_test_result = unit_test_functions.test_failed -- soft failure
        end
      end

      -- STEP 2: verify there is a lab available that can research this technology
      if not suitable_research_lab(tech_prototype) then
        local tech_ingredient_list = ""
        for _, lab_input_item_data in pairs(tech_prototype.research_unit_ingredients) do
          tech_ingredient_list = string.format(
            "%s%s%q",
            tech_ingredient_list,
            tech_ingredient_list == "" and "" or ", ",
            lab_input_item_data.name
          )
        end
        unit_test_functions.print_msg(
          string.format(
            "Technology %q cannot be researched, no lab accepts the required inputs (%s).",
            tech_name,
            tech_ingredient_list
          )
        )
        unit_test_result = unit_test_functions.test_failed -- soft failure
      end
    end
  end

  return unit_test_result
end

return {test_technologies_can_be_researched = test_technologies_can_be_researched}
