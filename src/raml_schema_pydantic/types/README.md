
# RAML Types in a nutshell:

- Types are similar to Java classes.
  - Types borrow additional features from JSON Schema, XSD, and more expressive object oriented languages.
- You can define types that inherit from other types.
  - Multiple inheritance is allowed.
- Types are split into four families: external, object, array, and scalar.
- Types can define two types of members: **properties** and **facets**. Both are inherited.
  - **Properties** are regular, object oriented properties.
  - **Facets** are special _configurations_. You specialize types based on characteristics of facet values.
    Examples: minLength, maxLength
 => **!!! Only facets are included in the type definitions !!!**
- Only object types can declare properties. All types can declare facets.
- To specialize a scalar type, you implement facets, giving already defined facets a concrete value.
- To specialize an object type, you define properties.
