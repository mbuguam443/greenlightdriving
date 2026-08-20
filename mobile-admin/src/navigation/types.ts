import { NavigatorScreenParams } from '@react-navigation/native';

export type AuthStackParamList = {
  Login: undefined;
};

export type HomeStackParamList = {
  Dashboard: undefined;
  Admissions: undefined;
  Chat: undefined;
  StudentDetail: { id: number; name?: string };
};

export type MoreStackParamList = {
  More: undefined;
  Profile: undefined;
  Notifications: undefined;
  Chat: undefined;
};

export type AppTabsParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  StudentsTab: undefined;
  PaymentsTab: undefined;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  App: NavigatorScreenParams<AppTabsParamList>;
};
