import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import EmailForm from "../components/EmailForm";
import CodeForm from "../components/CodeForm";

const Auth = () => {
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleEmailSubmit = async (emailInput: string) => {
    try {
      setLoading(true);
      await axios.post("/v1/auth/request_code", { email: emailInput });
      setEmail(emailInput);
      setStep("code");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Ошибка при отправке кода");
    } finally {
      setLoading(false);
    }
  };

  const handleCodeSubmit = async (code: string) => {
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
        alert("Неверный код или истёк срок действия");
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Ошибка проверки кода");
    } finally {
      setLoading(false);
    }
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
          <div className="w-full max-w-sm"> {/* Ограничиваем ширину формы */}
            {step === "email" && <EmailForm onSubmit={handleEmailSubmit} disabled={loading} />}
            {step === "code" && <CodeForm onSubmit={handleCodeSubmit} disabled={loading} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Auth;
