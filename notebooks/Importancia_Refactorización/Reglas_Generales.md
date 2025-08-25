# **Reglas Generales 📜**

Aquí te explico las maneras correctas y las convenciones más comunes para nombrar variables, funciones y clases en programación. Seguir estas reglas hace que tu código sea más legible, fácil de entender y mantener, tanto para ti como para otros desarrolladores.



Independientemente del lenguaje de programación, existen algunas reglas universales:

* **Nombres Descriptivos:** El nombre debe describir claramente lo que representa. Evita nombres de una sola letra (como `x` o `y`), a menos que sea en un contexto muy específico como un contador en un bucle (`i`).
    * **Mal:** `let d;`
    * **Bien:** `let diasTranscurridos;`
* **No Usar Palabras Reservadas:** No puedes usar palabras que el lenguaje de programación ya tiene reservadas para su sintaxis (como `if`, `for`, `class`, `while`, etc.).
* **Comenzar con una Letra:** Los nombres generalmente deben comenzar con una letra. Algunos lenguajes permiten que comiencen con un guion bajo (`_`) o un símbolo de dólar (`$`), pero esto suele tener un significado especial. Nunca deben empezar con un número.
* **Consistencia es Clave:** Elige un estilo y sé consistente a lo largo de todo tu proyecto.

---

## **1. Variables**

Las variables almacenan datos. Sus nombres deben ser sustantivos o frases nominales cortas que describan el dato que contienen. Los dos estilos más populares son:

* **camelCase:** La primera palabra comienza con minúscula y las siguientes palabras comienzan con mayúscula, sin espacios. Es el estándar en lenguajes como **JavaScript, Java, y C#**.
    * `let nombreDeUsuario = "JuanPerez";`
    * `const PI = 3.1416;` (Las constantes a menudo se escriben en mayúsculas, `UPPER_CASE_WITH_UNDERSCORES`, para distinguirlas).
    * `let edadMaximaPermitida = 99;`

* **snake_case:** Todas las palabras están en minúsculas y se separan por un guion bajo. Es el estándar en lenguajes como **Python y Ruby**.
    * `nombre_de_usuario = "JuanPerez"`
    * `PI = 3.1416`
    * `edad_maxima_permitida = 99`

---

## **2. Funciones**

Las funciones realizan acciones. Por lo tanto, sus nombres deben ser **verbos** o frases verbales que describan la acción que ejecutan. Al igual que con las variables, se usan principalmente `camelCase` o `snake_case` dependiendo del lenguaje.

* **Usa verbos de acción:**
    * `calcularImpuesto()`
    * `enviarFormulario()`
    * `obtenerDatosDelUsuario()`
    * `imprimir_reporte()` (en Python)

* **Para funciones que devuelven un valor booleano (verdadero/falso), es común empezar con `is`, `has` o `can`:**
    * `isLoggedIn()`
    * `hasPermission()`
    * `canExecute()`

La idea es que al leer el nombre de la función, sepas inmediatamente qué hace sin necesidad de ver su código interno.

---

## **3. Clases**

Las clases son plantillas o "moldes" para crear objetos. Representan conceptos, cosas o entidades. Por esta razón, sus nombres deben ser **sustantivos** y seguir una convención específica:

* **PascalCase (o UpperCamelCase):** Es similar a `camelCase`, pero la primera letra de *todas* las palabras, incluida la primera, es mayúscula. Esta es la convención estándar en la gran mayoría de los lenguajes de programación orientados a objetos como **Java, C++, C#, Python, JavaScript y PHP**.
    * `class Usuario { ... }`
    * `class GestorDeArchivos { ... }`
    * `class FacturaDeVenta { ... }`

El uso de `PascalCase` para las clases permite distinguirlas visualmente de las variables y funciones a simple vista.

## **Resumen de Estilos por Lenguaje**

| Elemento | Estilo Común | Lenguajes de Ejemplo | Ejemplo |
| :--- | :--- | :--- | :--- |
| **Variables** | `camelCase` | JavaScript, Java, C# | `let numeroDeIntentos;` |
| | `snake_case` | Python, Ruby | `numero_de_intentos = 0` |
| **Funciones** | `camelCase()` | JavaScript, Java, C# | `function calcularTotal() {}` |
| | `snake_case()` | Python, Ruby | `def calcular_total(): pass` |
| **Clases** | `PascalCase` | **Casi todos** (Python, Java, JS, C#) | `class HistorialDeCompras {}` |

Adoptar estas convenciones no solo es una buena práctica, sino que es fundamental para el trabajo en equipo y para escribir código profesional y sostenible a largo plazo.