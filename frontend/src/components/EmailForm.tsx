import { useForm } from "react-hook-form";
import PrimaryButton from "./PrimaryButton";

interface EmailFormProps {
  onSubmit: (email: string) => void;
  disabled?: boolean;
}

interface FormValues {
  email: string;
}

const EmailForm = ({ onSubmit, disabled }: EmailFormProps) => {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>();

  return (
    <form
      onSubmit={handleSubmit((data: FormValues) => onSubmit(data.email))}
      className="flex flex-col gap-2 w-full max-w-sm"
    >
      <input
        {...register("email", { required: true, pattern: /^\S+@\S+\.\S+$/i })}
        placeholder="Введите email"
        className="border p-3 rounded-4xl"
        disabled={disabled}
      />
      {errors.email && (
        <span className="text-sm text-red-600">
          {errors.email.type === 'required' ? 'Email обязателен' : 'Неверный формат email'}
        </span>
      )}
      <div className="flex justify-end">
        <PrimaryButton type="submit" className="w-full text-lg py-2">
          Получить код
        </PrimaryButton>
      </div>
    </form>
  );
};

export default EmailForm;
