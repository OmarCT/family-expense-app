import { StatusBar } from "expo-status-bar";
import { I18nextProvider, useTranslation } from "react-i18next";
import { StyleSheet, Text, View } from "react-native";

import { i18n } from "./src/i18n";

function Home() {
  const { t } = useTranslation();
  return (
    <View style={styles.container}>
      <Text>{t("app.title")}</Text>
      <StatusBar style="auto" />
    </View>
  );
}

export default function App() {
  return (
    <I18nextProvider i18n={i18n}>
      <Home />
    </I18nextProvider>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", alignItems: "center", justifyContent: "center" },
});
