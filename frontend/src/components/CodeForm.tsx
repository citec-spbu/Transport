import { useForm } from "react-hook-form";

interface CodeFormProps {
  onSubmit: (code: string) => void;
  disabled?: boolean;
}

interface FormValues {
  code: string;
}

const CodeForm = ({ onSubmit, disabled }: CodeFormProps) => {
  const { register, handleSubmit } = useForm<FormValues>();

  return (
    <form
      onSubmit={handleSubmit((data: FormValues) => onSubmit(data.code))}
      className="flex flex-col gap-2 w-full max-w-sm"
    >
      <input
        {...register("code", { required: true, maxLength: 6 })}
        placeholder="Введите код"
        className="border p-2 rounded"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled} className="bg-green-600 text-white p-2 rounded">
        Подтвердить код
      </button>
    </form>
  );
};

export default CodeForm;
