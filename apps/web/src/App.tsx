import { useTranslation } from "react-i18next";

export function App() {
  const { t } = useTranslation();
  return (
    <main>
      <h1>{t("app.title")}</h1>
    </main>
  );
}
