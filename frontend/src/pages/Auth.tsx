import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import EmailForm from "../components/EmailForm";
import CodeForm from "../components/CodeForm";
import PrimaryButton from "../components/PrimaryButton";

const Auth = () => {
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(""); // Для ошибок
  const [info, setInfo] = useState(""); // Для уведомлений (например, "Код отправлен")

  const navigate = useNavigate();

  const handleEmailSubmit = async (emailInput: string) => {
    setError("");
    try {
      setLoading(true);
      const response = await axios.post("/v1/auth/request_code", { email: emailInput });
      setEmail(emailInput);
      if (response.data.message === "User already verified") {
        navigate("/parameters");
        return;
      }
      setStep("code");
      setInfo(`Код отправлен на почту ${emailInput}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка при отправке кода");
    } finally {
      setLoading(false);
    }
  };

  const handleCodeSubmit = async (code: string) => {
    setError("");
    try {
      setLoading(true);
      const response = await axios.post("/v1/auth/verify_code", {
        email,
        code,
      });

      if (response.data.token) {
        localStorage.setItem("token", response.data.token);
        navigate("/parameters");
      } else {
        setError("Неверный код или истёк срок действия");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка проверки кода");
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError("");
    try {
      setLoading(true);
      const response = await axios.post("/v1/auth/guest");
      localStorage.setItem("token", response.data.token);
      navigate("/parameters");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка при гостевом входе");
    } finally {
      setLoading(false);
    }
  };

  const handleChangeEmail = () => {
    setStep("email");
    setInfo("");
    setEmail("");
  };

  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#f8f9fa]">
      <div
        className="absolute inset-0 bg-cover bg-center opacity-6"
        style={{ backgroundImage: "url('/images/background.png')" }}
      />
      <div className="relative z-10 flex flex-col h-full">
        <Header />
        <div className="flex flex-1 justify-center items-center">
          <div className="w-full max-w-sm flex flex-col gap-4">
            {step === "email" && (
              <>
                <h2 className="text-xl font-semibold text-center">Введите вашу почту</h2>
                <EmailForm onSubmit={handleEmailSubmit} disabled={loading} />
                {error && <div className="text-red-600 text-sm mt-1">{error}</div>}
                <PrimaryButton
                  onClick={handleGuestLogin}
                  disabled={loading}
                  className="mt-2 w-full py-2"
                >
                  Войти как гость
                </PrimaryButton>
              </>
            )}

            {step === "code" && (
              <>
                {info && (
                  <div className="text-center mb-2">
                    <span className="text-gray-700">{info}</span>
                    <button
                      onClick={handleChangeEmail}
                      className="ml-2 text-blue-600 underline hover:text-blue-800"
                    >
                      Изменить почту
                    </button>
                  </div>
                )}
                <h2 className="text-xl font-semibold text-center">Введите код из письма</h2>
                <CodeForm onSubmit={handleCodeSubmit} disabled={loading} />
                {error && <div className="text-red-600 text-sm mt-1">{error}</div>}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
