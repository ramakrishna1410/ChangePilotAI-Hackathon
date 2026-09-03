import { useState } from "react";
import { ChangeRequest } from "./api/client";
import { Dashboard } from "./pages/Dashboard";
import { Intake } from "./pages/Intake";
import { Analysis } from "./pages/Analysis";
import { Settings } from "./pages/Settings";

type View =
  | { name: "dashboard" }
  | { name: "intake" }
  | { name: "analysis"; cr: ChangeRequest; autoStart: boolean }
  | { name: "settings" };

export default function App() {
  const [view, setView] = useState<View>({ name: "dashboard" });

  if (view.name === "intake") {
    return (
      <Intake
        onCreated={(cr, autoStart) => setView({ name: "analysis", cr, autoStart })}
      />
    );
  }

  if (view.name === "analysis") {
    return (
      <Analysis cr={view.cr} autoStart={view.autoStart} onBack={() => setView({ name: "dashboard" })} />
    );
  }

  if (view.name === "settings") {
    return <Settings onBack={() => setView({ name: "dashboard" })} />;
  }

  return (
    <Dashboard
      onNewCr={() => setView({ name: "intake" })}
      onSelectCr={(cr) => setView({ name: "analysis", cr, autoStart: false })}
      onSettings={() => setView({ name: "settings" })}
    />
  );
}
