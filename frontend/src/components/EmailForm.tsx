import { useForm } from "react-hook-form";

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
        className="border p-2 rounded"
        disabled={disabled}
      />
      {errors.email && (
        <span className="text-sm text-red-600">
          {errors.email.type === 'required' ? 'Email обязателен' : 'Неверный формат email'}
        </span>
      )}
      <button type="submit" disabled={disabled} className="bg-blue-600 text-white p-2 rounded">
        Получить код
      </button>
    </form>
  );
};

export default EmailForm;
