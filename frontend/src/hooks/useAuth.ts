import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';
import { useAuthStore } from '@/stores/authStore';
import { ROUTES } from '@/constants';
import type { LoginRequest, RegisterRequest } from '@/types';

export function useAuth() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, setAuth, logout: storeLogout } = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: (data: LoginRequest) => api.auth.login(data),
    onSuccess: (response) => {
      const { user, token } = response.data;
      setAuth(user, token.access_token);
      queryClient.invalidateQueries({ queryKey: ['user'] });
      navigate(ROUTES.DASHBOARD);
    },
  });

  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => api.auth.register(data),
    onSuccess: (response) => {
      const { user, token } = response.data;
      setAuth(user, token.access_token);
      queryClient.invalidateQueries({ queryKey: ['user'] });
      navigate(ROUTES.DASHBOARD);
    },
  });

  const { data: currentUser, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user', 'me'],
    queryFn: () => api.auth.me(),
    enabled: isAuthenticated,
    select: (response) => response.data,
  });

  const logout = () => {
    storeLogout();
    queryClient.clear();
    navigate(ROUTES.LOGIN);
  };

  return {
    user: currentUser ?? user,
    isAuthenticated,
    isLoading: loginMutation.isPending || registerMutation.isPending,
    isLoadingUser,
    error: loginMutation.error || registerMutation.error,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
  };
}
