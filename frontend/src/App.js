import { useEffect } from "react";

// UrduDuo app is rendered as static HTML in public/index.html.
// This React component intentionally renders nothing.
function App() {
  useEffect(() => {
    // Show static app, hide React root container.
    const root = document.getElementById("root");
    if (root) root.style.display = "none";
  }, []);
  return null;
}

export default App;
